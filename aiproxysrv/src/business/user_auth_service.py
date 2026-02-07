"""
User Authentication Business Service

Pure authentication logic (password hashing, JWT tokens)
- NO database operations
- NO file system operations
- Fully unit-testable without mocks
"""

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from config.settings import JWT_ALGORITHM, JWT_EXPIRATION_HOURS, JWT_SECRET_KEY
from utils.logger import logger


class UserAuthService:
    """User authentication business logic (pure functions)"""

    def __init__(self):
        """Initialize authentication service with JWT configuration"""
        self.jwt_secret = JWT_SECRET_KEY
        self.jwt_algorithm = JWT_ALGORITHM
        self.jwt_expiration_hours = JWT_EXPIRATION_HOURS

    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt

        Args:
            password: Plain text password

        Returns:
            Hashed password string

        Example:
            >>> auth_service = UserAuthService()
            >>> hashed = auth_service.hash_password("mypassword123")
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        logger.debug("Password hashed successfully")
        return hashed.decode("utf-8")

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify password against hash

        Args:
            password: Plain text password to verify
            hashed_password: Hashed password from database

        Returns:
            True if password matches, False otherwise

        Example:
            >>> auth_service = UserAuthService()
            >>> is_valid = auth_service.verify_password("mypassword123", hashed)
        """
        try:
            result = bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
            if result:
                logger.debug("Password verified successfully")
            else:
                logger.debug("Password verification failed")
            return result
        except Exception as e:
            logger.warning("Password verification error", error=str(e))
            return False

    def generate_jwt_token(self, user_id: str, email: str) -> str:
        """
        Generate JWT token for user authentication

        Args:
            user_id: User UUID as string
            email: User email address

        Returns:
            JWT token string

        Example:
            >>> auth_service = UserAuthService()
            >>> token = auth_service.generate_jwt_token("123e4567-...", "user@example.com")
        """
        payload = {
            "user_id": str(user_id),
            "email": email,
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC) + timedelta(hours=self.jwt_expiration_hours),
        }
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        logger.debug("JWT token generated", user_id=user_id, email=email)
        return token

    def verify_jwt_token(self, token: str) -> dict | None:
        """
        Verify JWT token and return payload if valid

        Args:
            token: JWT token string

        Returns:
            Token payload dict if valid, None if invalid/expired

        Example:
            >>> auth_service = UserAuthService()
            >>> payload = auth_service.verify_jwt_token(token)
            >>> if payload:
            ...     user_id = payload.get("user_id")
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            logger.debug("JWT token verified successfully", user_id=payload.get("user_id"))
            return payload
        except jwt.ExpiredSignatureError:
            logger.debug("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.debug("JWT token invalid", error=str(e))
            return None

    def validate_password_strength(self, password: str) -> tuple[bool, str | None]:
        """
        Validate password strength

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, error_message)

        Example:
            >>> auth_service = UserAuthService()
            >>> is_valid, error = auth_service.validate_password_strength("weak")
            >>> if not is_valid:
            ...     print(error)
        """
        if not password:
            return False, "Password cannot be empty"

        if len(password) < 8:
            return False, "Password must be at least 8 characters long"

        # Additional strength checks can be added here
        # - Contains uppercase
        # - Contains lowercase
        # - Contains number
        # - Contains special character

        return True, None
