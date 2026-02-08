"""Usage Log Service - Database operations for AI usage tracking (CRUD only)"""

import uuid

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.models import UsageLog
from utils.logger import logger


class UsageLogService:
    """Service for usage log database operations"""

    def create_log(
        self,
        db: Session,
        user_id: str,
        endpoint: str,
        model: str,
        category: str | None = None,
        action: str | None = None,
        prompt_tokens: int | None = None,
        eval_tokens: int | None = None,
        total_duration_ns: int | None = None,
    ) -> UsageLog | None:
        """
        Create a new usage log entry.

        Args:
            db: Database session
            user_id: UUID of the user
            endpoint: API endpoint (e.g. "generate-unified")
            model: AI model used
            category: Template category (optional)
            action: Template action (optional)
            prompt_tokens: From Ollama prompt_eval_count (optional)
            eval_tokens: From Ollama eval_count (optional)
            total_duration_ns: From Ollama total_duration in nanoseconds (optional)

        Returns:
            UsageLog instance if successful, None otherwise
        """
        try:
            log_entry = UsageLog(
                id=uuid.uuid4(),
                user_id=user_id,
                endpoint=endpoint,
                model=model,
                category=category,
                action=action,
                prompt_tokens=prompt_tokens,
                eval_tokens=eval_tokens,
                total_duration_ns=total_duration_ns,
            )

            db.add(log_entry)
            db.commit()

            logger.debug(
                "Usage log created",
                user_id=user_id,
                endpoint=endpoint,
                model=model,
                category=category,
                action=action,
            )
            return log_entry

        except SQLAlchemyError as e:
            db.rollback()
            logger.error("usage_log_creation_db_error", error=str(e), error_type=type(e).__name__)
            return None
        except Exception as e:
            logger.error("usage_log_creation_failed", error=str(e), error_type=type(e).__name__)
            return None
