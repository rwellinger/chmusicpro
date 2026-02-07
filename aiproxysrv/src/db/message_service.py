"""Message Service - Database operations for message management (CRUD only, no business logic)."""

import traceback
import uuid
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.models import Message, MessageArchive
from utils.logger import logger


class MessageService:
    """Service for message database operations (CRUD only)."""

    def get_conversation_messages(self, db: Session, conversation_id: uuid.UUID) -> list[Message]:
        """
        Get all messages for a conversation, ordered by creation date.

        Args:
            db: Database session
            conversation_id: Conversation UUID

        Returns:
            List of Message objects
        """
        try:
            messages = (
                db.query(Message)
                .filter(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.asc())
                .all()
            )

            logger.debug("Messages retrieved", conversation_id=str(conversation_id), count=len(messages))
            return messages

        except SQLAlchemyError as e:
            logger.error(
                "Database error retrieving messages",
                conversation_id=str(conversation_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            return []

    def create_message(
        self,
        db: Session,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        token_count: int = 0,
        is_summary: bool = False,
    ) -> Message | None:
        """
        Create a new message in the database.

        Args:
            db: Database session
            conversation_id: Conversation UUID
            role: Message role (system, user, assistant)
            content: Message content
            token_count: Token count for the message
            is_summary: Whether this is a summary message

        Returns:
            Message object if successful, None otherwise
        """
        try:
            message = Message(
                id=uuid.uuid4(),
                conversation_id=conversation_id,
                role=role,
                content=content,
                token_count=token_count,
                is_summary=is_summary,
                created_at=datetime.utcnow(),
            )

            db.add(message)
            db.flush()  # Flush to get the ID without committing

            logger.debug(
                "Message created",
                message_id=str(message.id),
                conversation_id=str(conversation_id),
                role=role,
                is_summary=is_summary,
            )

            return message

        except SQLAlchemyError as e:
            logger.error(
                "Database error creating message",
                conversation_id=str(conversation_id),
                error=str(e),
                error_type=type(e).__name__,
                stacktrace=traceback.format_exc(),
            )
            return None

    def archive_messages(self, db: Session, messages: list[Message], summary_message_id: uuid.UUID) -> int:
        """
        Archive messages by moving them to messages_archive table.

        Args:
            db: Database session
            messages: List of messages to archive
            summary_message_id: ID of the summary message

        Returns:
            Number of archived messages
        """
        archived_count = 0

        try:
            for msg in messages:
                # Create archive entry
                archive = MessageArchive(
                    id=uuid.uuid4(),
                    original_message_id=msg.id,
                    conversation_id=msg.conversation_id,
                    role=msg.role,
                    content=msg.content,
                    token_count=msg.token_count,
                    original_created_at=msg.created_at,
                    summary_message_id=summary_message_id,
                )
                db.add(archive)

                # Delete original message
                db.delete(msg)
                archived_count += 1

            logger.debug("Messages archived", count=archived_count, summary_id=str(summary_message_id))
            return archived_count

        except SQLAlchemyError as e:
            logger.error(
                "Database error archiving messages",
                error=str(e),
                error_type=type(e).__name__,
                stacktrace=traceback.format_exc(),
            )
            return 0

    def get_archived_messages(self, db: Session, conversation_id: uuid.UUID) -> list[MessageArchive]:
        """
        Get archived messages for a conversation.

        Args:
            db: Database session
            conversation_id: Conversation UUID

        Returns:
            List of MessageArchive objects
        """
        try:
            archived = (
                db.query(MessageArchive)
                .filter(MessageArchive.conversation_id == conversation_id)
                .order_by(MessageArchive.original_created_at.asc())
                .all()
            )

            logger.debug("Archived messages retrieved", conversation_id=str(conversation_id), count=len(archived))
            return archived

        except SQLAlchemyError as e:
            logger.error(
                "Database error retrieving archived messages",
                conversation_id=str(conversation_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            return []

    def restore_archived_messages(self, db: Session, conversation_id: uuid.UUID) -> int:
        """
        Restore archived messages for a conversation.

        Args:
            db: Database session
            conversation_id: Conversation UUID

        Returns:
            Number of restored messages
        """
        restored_count = 0

        try:
            # Get archived messages
            archived_messages = self.get_archived_messages(db, conversation_id)

            if not archived_messages:
                return 0

            # Restore each archived message
            for archive in archived_messages:
                # Create message from archive
                msg = Message(
                    id=archive.original_message_id,
                    conversation_id=archive.conversation_id,
                    role=archive.role,
                    content=archive.content,
                    token_count=archive.token_count,
                    is_summary=False,
                    created_at=archive.original_created_at,
                )
                db.add(msg)

                # Delete archive entry
                db.delete(archive)
                restored_count += 1

            logger.debug("Archived messages restored", conversation_id=str(conversation_id), count=restored_count)
            return restored_count

        except SQLAlchemyError as e:
            logger.error(
                "Database error restoring archived messages",
                conversation_id=str(conversation_id),
                error=str(e),
                error_type=type(e).__name__,
                stacktrace=traceback.format_exc(),
            )
            return 0

    def delete_message(self, db: Session, message_id: uuid.UUID) -> bool:
        """
        Delete a message by ID.

        Args:
            db: Database session
            message_id: Message UUID

        Returns:
            True if successful, False otherwise
        """
        try:
            message = db.query(Message).filter(Message.id == message_id).first()

            if not message:
                logger.warning("Message not found for deletion", message_id=str(message_id))
                return False

            db.delete(message)
            logger.debug("Message deleted", message_id=str(message_id))
            return True

        except SQLAlchemyError as e:
            logger.error(
                "Database error deleting message",
                message_id=str(message_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            return False
