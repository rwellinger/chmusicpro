"""
User Service for database operations (CRUD only)

Pure database operations - NO business logic, NO authentication logic
All authentication logic moved to business.user_auth_service
"""

import uuid
from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.models import User
from utils.logger import logger


class UserService:
    """User database operations (CRUD only)"""

    def create_user(
        self,
        db: Session,
        email: str,
        password_hash: str,
        first_name: str = None,
        last_name: str = None,
    ) -> User | None:
        """
        Create a new user (expects hashed password)

        Args:
            db: Database session
            email: User email address
            password_hash: Pre-hashed password from UserAuthService
            first_name: Optional first name
            last_name: Optional last name

        Returns:
            Created User object or None

        Note: Password must be hashed by UserAuthService before calling this method
        """
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                logger.warning("User creation failed - email already exists", email=email)
                raise ValueError(f"User with email {email} already exists")

            # Create the user with hashed password
            user = User(
                id=uuid.uuid4(),
                email=email,
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                is_verified=False,
                created_at=datetime.utcnow(),
            )

            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("User created", user_id=str(user.id), email=email)
            return user

        except IntegrityError:
            db.rollback()
            logger.error("User creation failed - integrity error", email=email)
            raise ValueError(f"User with email {email} already exists")
        except Exception as e:
            db.rollback()
            logger.error("User creation failed", error=str(e), email=email)
            raise e

    def get_user_by_id(self, db: Session, user_id: str) -> User | None:
        """
        Get user by ID

        Args:
            db: Database session
            user_id: User UUID as string

        Returns:
            User object or None if not found
        """
        try:
            user_uuid = uuid.UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid, User.is_active).first()
            if user:
                logger.debug("User retrieved by ID", user_id=user_id)
            return user
        except (ValueError, TypeError) as e:
            logger.warning("Invalid user ID format", user_id=user_id, error=str(e))
            return None

    def get_user_by_email(self, db: Session, email: str) -> User | None:
        """
        Get user by email

        Args:
            db: Database session
            email: User email address

        Returns:
            User object or None if not found
        """
        user = db.query(User).filter(User.email == email, User.is_active).first()
        if user:
            logger.debug("User retrieved by email", email=email, user_id=str(user.id))
        return user

    def update_user(
        self,
        db: Session,
        user_id: str,
        first_name: str = None,
        last_name: str = None,
        artist_name: str = None,
    ) -> User | None:
        """
        Update user information

        Args:
            db: Database session
            user_id: User UUID as string
            first_name: Optional first name
            last_name: Optional last name
            artist_name: Optional artist name

        Returns:
            Updated User object or None if not found
        """
        try:
            user_uuid = uuid.UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid, User.is_active).first()

            if not user:
                logger.warning("User update failed - user not found", user_id=user_id)
                return None

            # Update fields if provided
            if first_name is not None:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name
            if artist_name is not None:
                user.artist_name = artist_name

            user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
            logger.info("User updated", user_id=user_id)
            return user

        except (ValueError, TypeError) as e:
            logger.warning("Invalid user ID format", user_id=user_id, error=str(e))
            return None
        except Exception as e:
            db.rollback()
            logger.error("User update failed", error=str(e), user_id=user_id)
            raise e

    def update_password_hash(self, db: Session, user_id: str, password_hash: str) -> bool:
        """
        Update user password hash (expects pre-hashed password)

        Args:
            db: Database session
            user_id: User UUID as string
            password_hash: Pre-hashed password from UserAuthService

        Returns:
            True if successful, False otherwise

        Note: Password must be hashed by UserAuthService before calling this method
        """
        try:
            user_uuid = uuid.UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid, User.is_active).first()

            if not user:
                logger.warning("Password update failed - user not found", user_id=user_id)
                return False

            user.password_hash = password_hash
            user.updated_at = datetime.utcnow()
            db.commit()
            logger.info("User password updated", user_id=user_id)
            return True

        except (ValueError, TypeError) as e:
            logger.warning("Invalid user ID format", user_id=user_id, error=str(e))
            return False
        except Exception as e:
            db.rollback()
            logger.error("Password update failed", error=str(e), user_id=user_id)
            raise e

    def update_last_login(self, db: Session, user_id: str) -> bool:
        """
        Update user's last login timestamp

        Args:
            db: Database session
            user_id: User UUID as string

        Returns:
            True if successful, False otherwise
        """
        try:
            user_uuid = uuid.UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid, User.is_active).first()

            if not user:
                return False

            user.last_login = datetime.utcnow()
            db.commit()
            logger.debug("Last login updated", user_id=user_id)
            return True

        except (ValueError, TypeError):
            return False
        except Exception as e:
            db.rollback()
            logger.error("Last login update failed", error=str(e), user_id=user_id)
            raise e

    def deactivate_user(self, db: Session, user_id: str) -> bool:
        """
        Deactivate a user (soft delete)

        Args:
            db: Database session
            user_id: User UUID as string

        Returns:
            True if successful, False otherwise
        """
        try:
            user_uuid = uuid.UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid).first()

            if not user:
                logger.warning("User deactivation failed - user not found", user_id=user_id)
                return False

            user.is_active = False
            user.updated_at = datetime.utcnow()
            db.commit()
            logger.info("User deactivated", user_id=user_id)
            return True

        except (ValueError, TypeError) as e:
            logger.warning("Invalid user ID format", user_id=user_id, error=str(e))
            return False
        except Exception as e:
            db.rollback()
            logger.error("User deactivation failed", error=str(e), user_id=user_id)
            raise e

    def list_users(self, db: Session, skip: int = 0, limit: int = 100) -> list[User]:
        """
        List all active users

        Args:
            db: Database session
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return

        Returns:
            List of User objects
        """
        users = db.query(User).filter(User.is_active).offset(skip).limit(limit).all()
        logger.debug("Users listed", count=len(users), skip=skip, limit=limit)
        return users
