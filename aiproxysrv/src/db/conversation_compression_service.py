"""Conversation Compression Service - Handles atomic compression operations with transaction management."""

import uuid

from sqlalchemy.orm import Session

from db.conversation_service import ConversationService
from db.message_service import MessageService
from utils.logger import logger


class ConversationCompressionService:
    """Service for atomic conversation compression operations (with transaction management)."""

    def __init__(self):
        self.message_service = MessageService()
        self.conversation_service = ConversationService()

    def commit_compression(
        self,
        db: Session,
        conversation_id: uuid.UUID,
        summary_content: str,
        summary_token_count: int,
        old_messages: list,
        actual_token_count: int,
    ) -> int:
        """
        Commit compression changes as atomic transaction.

        Args:
            db: Database session
            conversation_id: Conversation UUID
            summary_content: Formatted summary message content
            summary_token_count: Token count for summary
            old_messages: Messages to archive
            actual_token_count: New total token count

        Returns:
            Number of archived messages

        Raises:
            Exception: If any database operation fails (with automatic rollback)
        """
        try:
            # Create summary message
            summary_message = self.message_service.create_message(
                db=db,
                conversation_id=conversation_id,
                role="assistant",
                content=summary_content,
                token_count=summary_token_count,
                is_summary=True,
            )

            if not summary_message:
                raise Exception("Failed to create summary message")

            # Archive old messages
            archived_count = self.message_service.archive_messages(db, old_messages, summary_message.id)

            # Update conversation token count
            self.conversation_service.update_token_count(db, conversation_id, actual_token_count)

            # Commit transaction
            db.commit()

            logger.info(
                "Compression committed successfully",
                conversation_id=str(conversation_id),
                archived_count=archived_count,
                new_token_count=actual_token_count,
            )

            return archived_count

        except Exception as e:
            db.rollback()
            logger.error(
                "Failed to commit compression",
                conversation_id=str(conversation_id),
                error_type=type(e).__name__,
                error=str(e),
            )
            raise

    def commit_restore(
        self,
        db: Session,
        conversation_id: uuid.UUID,
        summary_id: uuid.UUID | None,
        total_tokens: int,
    ) -> int:
        """
        Commit archive restoration as atomic transaction.

        Args:
            db: Database session
            conversation_id: Conversation UUID
            summary_id: Summary message UUID to delete (if exists)
            total_tokens: New total token count

        Returns:
            Number of restored messages

        Raises:
            Exception: If any database operation fails (with automatic rollback)
        """
        try:
            # Restore archived messages
            restored_count = self.message_service.restore_archived_messages(db, conversation_id)

            # Delete summary message if exists
            if summary_id:
                self.message_service.delete_message(db, summary_id)

            # Update conversation token count
            self.conversation_service.update_token_count(db, conversation_id, total_tokens)

            # Commit transaction
            db.commit()

            logger.info(
                "Archive restoration committed successfully",
                conversation_id=str(conversation_id),
                restored_count=restored_count,
                new_token_count=total_tokens,
            )

            return restored_count

        except Exception as e:
            db.rollback()
            logger.error(
                "Failed to commit archive restoration",
                conversation_id=str(conversation_id),
                error_type=type(e).__name__,
                error=str(e),
            )
            raise
