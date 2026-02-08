"""
Registration Log Service for database operations (CRUD only)

Pure database operations - NO business logic
Logs registration attempts for audit purposes.
"""

import uuid

from sqlalchemy.orm import Session

from db.models import RegistrationLog
from utils.logger import logger


class RegistrationLogService:
    """Registration log database operations (CRUD only)"""

    def create_log(
        self,
        db: Session,
        email: str,
        first_name: str = None,
        last_name: str = None,
        preferred_language: str = "en",
        ip_address: str = None,
        user_agent: str = None,
    ) -> RegistrationLog:
        """
        Create a registration log entry.

        Args:
            db: Database session
            email: Registered email address
            first_name: Optional first name
            last_name: Optional last name
            preferred_language: User's preferred language
            ip_address: Client IP address
            user_agent: Client user agent string

        Returns:
            Created RegistrationLog object
        """
        log_entry = RegistrationLog(
            id=uuid.uuid4(),
            email=email,
            first_name=first_name,
            last_name=last_name,
            preferred_language=preferred_language,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        db.add(log_entry)
        db.commit()
        logger.info("Registration logged", email=email, ip_address=ip_address)
        return log_entry
