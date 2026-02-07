"""
User Controller for handling user authentication and management

Uses 3-Layer Architecture:
- Controller (this file): HTTP handling, request/response formatting
- Business (UserAuthService): Authentication logic, password hashing, JWT
- Repository (UserService): Database CRUD operations
"""

from datetime import datetime, timedelta
from typing import Any

from business.user_auth_service import UserAuthService
from db.database import SessionLocal
from db.user_service import UserService
from schemas.common_schemas import ErrorResponse
from schemas.user_schemas import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    PasswordChangeRequest,
    PasswordChangeResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    UserCreateRequest,
    UserCreateResponse,
    UserListResponse,
    UserResponse,
    UserUpdateRequest,
    UserUpdateResponse,
)
from utils.logger import logger


class UserController:
    """Controller for user authentication and management operations"""

    def __init__(self):
        self.user_service = UserService()
        self.auth_service = UserAuthService()

    def _get_db(self):
        """Get database session"""
        return SessionLocal()

    def _format_error_response(self, message: str, status_code: int = 400) -> tuple[dict[str, Any], int]:
        """Format error response"""
        error_response = ErrorResponse(error=message)
        return error_response.model_dump(), status_code

    def _format_success_response(self, response_model, status_code: int = 200) -> tuple[dict[str, Any], int]:
        """Format success response"""
        return response_model.model_dump(), status_code

    def create_user(self, request: UserCreateRequest) -> tuple[dict[str, Any], int]:
        """Create a new user"""
        db = self._get_db()
        try:
            # Business logic: Validate password strength
            is_valid, error_msg = self.auth_service.validate_password_strength(request.password)
            if not is_valid:
                return self._format_error_response(error_msg, 400)

            # Business logic: Hash password
            password_hash = self.auth_service.hash_password(request.password)

            # Repository: Create user
            user = self.user_service.create_user(
                db=db,
                email=request.email,
                password_hash=password_hash,
                first_name=request.first_name,
                last_name=request.last_name,
            )

            if not user:
                return self._format_error_response("Failed to create user", 500)

            response = UserCreateResponse(
                success=True, message="User created successfully", user_id=user.id, email=user.email
            )
            return self._format_success_response(response, 201)

        except ValueError as e:
            return self._format_error_response(str(e), 400)
        except Exception as e:
            logger.error("Error creating user", error=str(e))
            return self._format_error_response("Internal server error", 500)
        finally:
            db.close()

    def login(self, request: LoginRequest) -> tuple[dict[str, Any], int]:
        """Authenticate user and return JWT token"""
        db = self._get_db()
        try:
            # Repository: Get user by email
            user = self.user_service.get_user_by_email(db, request.email)

            if not user or not user.password_hash:
                logger.debug("Login failed - user not found or no password", email=request.email)
                return self._format_error_response("Invalid email or password", 401)

            # Business logic: Verify password
            if not self.auth_service.verify_password(request.password, user.password_hash):
                logger.debug("Login failed - invalid password", email=request.email)
                return self._format_error_response("Invalid email or password", 401)

            # Repository: Update last login timestamp
            self.user_service.update_last_login(db, str(user.id))

            # Business logic: Generate JWT token
            token = self.auth_service.generate_jwt_token(str(user.id), user.email)

            # Create response
            user_response = UserResponse.model_validate(user)
            expires_at = datetime.utcnow() + timedelta(hours=self.auth_service.jwt_expiration_hours)

            response = LoginResponse(
                success=True, message="Login successful", token=token, user=user_response, expires_at=expires_at
            )
            logger.info("User logged in successfully", user_id=str(user.id), email=user.email)
            return self._format_success_response(response, 200)

        except Exception as e:
            logger.error("Error during login", error=str(e))
            return self._format_error_response("Internal server error", 500)
        finally:
            db.close()

    def logout(self) -> tuple[dict[str, Any], int]:
        """Logout user (token invalidation would happen on frontend)"""
        response = LogoutResponse(success=True, message="Logout successful")
        return self._format_success_response(response, 200)

    def get_user_profile(self, user_id: str) -> tuple[dict[str, Any], int]:
        """Get user profile by ID"""
        db = self._get_db()
        try:
            user = self.user_service.get_user_by_id(db, user_id)

            if not user:
                return self._format_error_response("User not found", 404)

            user_response = UserResponse.model_validate(user)
            return self._format_success_response(user_response, 200)

        except Exception as e:
            logger.error("Error getting user profile", error=str(e))
            return self._format_error_response("Internal server error", 500)
        finally:
            db.close()

    def update_user(self, user_id: str, request: UserUpdateRequest) -> tuple[dict[str, Any], int]:
        """Update user information"""
        db = self._get_db()
        try:
            user = self.user_service.update_user(
                db=db,
                user_id=user_id,
                first_name=request.first_name,
                last_name=request.last_name,
                artist_name=request.artist_name,
            )

            if not user:
                return self._format_error_response("User not found", 404)

            user_response = UserResponse.model_validate(user)
            response = UserUpdateResponse(success=True, message="User updated successfully", user=user_response)
            return self._format_success_response(response, 200)

        except Exception as e:
            logger.error("Error updating user", error=str(e))
            return self._format_error_response("Internal server error", 500)
        finally:
            db.close()

    def change_password(self, user_id: str, request: PasswordChangeRequest) -> tuple[dict[str, Any], int]:
        """Change user password"""
        db = self._get_db()
        try:
            # Repository: Get user
            user = self.user_service.get_user_by_id(db, user_id)

            if not user or not user.password_hash:
                logger.debug("Password change failed - user not found", user_id=user_id)
                return self._format_error_response("User not found", 404)

            # Business logic: Verify old password
            if not self.auth_service.verify_password(request.old_password, user.password_hash):
                logger.debug("Password change failed - invalid old password", user_id=user_id)
                return self._format_error_response("Invalid current password", 400)

            # Business logic: Validate new password strength
            is_valid, error_msg = self.auth_service.validate_password_strength(request.new_password)
            if not is_valid:
                return self._format_error_response(error_msg, 400)

            # Business logic: Hash new password
            new_password_hash = self.auth_service.hash_password(request.new_password)

            # Repository: Update password hash
            success = self.user_service.update_password_hash(db, user_id, new_password_hash)

            if not success:
                return self._format_error_response("Failed to update password", 500)

            response = PasswordChangeResponse(success=True, message="Password changed successfully")
            logger.info("Password changed successfully", user_id=user_id)
            return self._format_success_response(response, 200)

        except Exception as e:
            logger.error("Error changing password", error=str(e), user_id=user_id)
            return self._format_error_response("Internal server error", 500)
        finally:
            db.close()

    def reset_password(self, request: PasswordResetRequest) -> tuple[dict[str, Any], int]:
        """Reset user password (admin function)"""
        db = self._get_db()
        try:
            # Repository: Get user by email
            user = self.user_service.get_user_by_email(db, request.email)

            if not user:
                logger.debug("Password reset failed - user not found", email=request.email)
                return self._format_error_response("User not found", 404)

            # Business logic: Validate new password strength
            is_valid, error_msg = self.auth_service.validate_password_strength(request.new_password)
            if not is_valid:
                return self._format_error_response(error_msg, 400)

            # Business logic: Hash new password
            new_password_hash = self.auth_service.hash_password(request.new_password)

            # Repository: Update password hash
            success = self.user_service.update_password_hash(db, str(user.id), new_password_hash)

            if not success:
                return self._format_error_response("Failed to reset password", 500)

            response = PasswordResetResponse(success=True, message="Password reset successfully")
            logger.info("Password reset successfully", email=request.email, user_id=str(user.id))
            return self._format_success_response(response, 200)

        except Exception as e:
            logger.error("Error resetting password", error=str(e), email=request.email)
            return self._format_error_response("Internal server error", 500)
        finally:
            db.close()

    def list_users(self, skip: int = 0, limit: int = 100) -> tuple[dict[str, Any], int]:
        """List all users (admin function)"""
        db = self._get_db()
        try:
            users = self.user_service.list_users(db, skip, limit)

            users_response = [UserResponse.model_validate(user) for user in users]
            response = UserListResponse(
                success=True, message="Users retrieved successfully", users=users_response, total=len(users_response)
            )
            return self._format_success_response(response, 200)

        except Exception as e:
            logger.error("Error listing users", error=str(e))
            return self._format_error_response("Internal server error", 500)
        finally:
            db.close()

    def validate_token(self, token: str) -> dict[str, Any] | None:
        """Validate JWT token and return user info (with database check)"""
        db = self._get_db()
        try:
            # Business logic: Verify JWT token
            payload = self.auth_service.verify_jwt_token(token)
            if not payload:
                return None

            # Repository: Verify user still exists in database
            user = self.user_service.get_user_by_id(db, payload.get("user_id"))
            if not user:
                logger.warning("Token valid but user not found in database", user_id=payload.get("user_id"))
                return None

            return {"user_id": payload.get("user_id"), "email": payload.get("email")}
        except Exception as e:
            logger.error("Error validating token", error=str(e))
            return None
        finally:
            db.close()

    def validate_token_light(self, token: str) -> dict[str, Any] | None:
        """Lightweight JWT token validation (no database check)"""
        try:
            # Business logic: Verify JWT token
            payload = self.auth_service.verify_jwt_token(token)
            if payload:
                return {"user_id": payload.get("user_id"), "email": payload.get("email")}
            return None
        except Exception as e:
            logger.error("Error validating token (light)", error=str(e))
            return None
