"""Conversation Service - Database operations for conversation management (CRUD only, no business logic)."""

import traceback
import uuid
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.models import Conversation
from utils.logger import logger


class ConversationService:
    """Service for conversation database operations (CRUD only)."""

    def get_conversation(self, db: Session, conversation_id: uuid.UUID, user_id: uuid.UUID) -> Conversation | None:
        """
        Get conversation by ID and user ID.

        Args:
            db: Database session
            conversation_id: Conversation UUID
            user_id: User UUID

        Returns:
            Conversation object if found, None otherwise
        """
        try:
            conversation = (
                db.query(Conversation)
                .filter(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id,
                )
                .first()
            )

            if conversation:
                logger.debug("Conversation retrieved", conversation_id=str(conversation_id), user_id=str(user_id))
            else:
                logger.warning("Conversation not found", conversation_id=str(conversation_id), user_id=str(user_id))

            return conversation

        except SQLAlchemyError as e:
            logger.error(
                "Database error retrieving conversation",
                conversation_id=str(conversation_id),
                user_id=str(user_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            return None

    def update_token_count(self, db: Session, conversation_id: uuid.UUID, token_count: int) -> bool:
        """
        Update conversation token count and updated_at timestamp.

        Args:
            db: Database session
            conversation_id: Conversation UUID
            token_count: New token count

        Returns:
            True if successful, False otherwise
        """
        try:
            conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()

            if not conversation:
                logger.warning("Conversation not found for token count update", conversation_id=str(conversation_id))
                return False

            conversation.current_token_count = token_count
            conversation.updated_at = datetime.utcnow()

            logger.debug(
                "Conversation token count updated",
                conversation_id=str(conversation_id),
                token_count=token_count,
            )
            return True

        except SQLAlchemyError as e:
            logger.error(
                "Database error updating conversation token count",
                conversation_id=str(conversation_id),
                error=str(e),
                error_type=type(e).__name__,
                stacktrace=traceback.format_exc(),
            )
            return False

    def create_conversation(
        self,
        db: Session,
        user_id: uuid.UUID,
        title: str,
        model: str,
        provider: str,
        context_window_size: int,
    ) -> Conversation | None:
        """
        Create a new conversation.

        Args:
            db: Database session
            user_id: User UUID
            title: Conversation title
            model: Model name
            provider: Provider ('internal' or 'external')
            context_window_size: Context window size in tokens

        Returns:
            Conversation object if successful, None otherwise
        """
        try:
            conversation = Conversation(
                id=uuid.uuid4(),
                user_id=user_id,
                title=title,
                model=model,
                provider=provider,
                context_window_size=context_window_size,
                current_token_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            db.add(conversation)
            db.flush()  # Flush to get the ID

            logger.info(
                "Conversation created",
                conversation_id=str(conversation.id),
                user_id=str(user_id),
                model=model,
                provider=provider,
            )

            return conversation

        except SQLAlchemyError as e:
            logger.error(
                "Database error creating conversation",
                user_id=str(user_id),
                error=str(e),
                error_type=type(e).__name__,
                stacktrace=traceback.format_exc(),
            )
            return None

    def delete_conversation(self, db: Session, conversation_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """
        Delete a conversation by ID and user ID.

        Args:
            db: Database session
            conversation_id: Conversation UUID
            user_id: User UUID

        Returns:
            True if successful, False otherwise
        """
        try:
            conversation = self.get_conversation(db, conversation_id, user_id)

            if not conversation:
                logger.warning(
                    "Conversation not found for deletion", conversation_id=str(conversation_id), user_id=str(user_id)
                )
                return False

            db.delete(conversation)
            logger.info("Conversation deleted", conversation_id=str(conversation_id), user_id=str(user_id))
            return True

        except SQLAlchemyError as e:
            logger.error(
                "Database error deleting conversation",
                conversation_id=str(conversation_id),
                user_id=str(user_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            return False
