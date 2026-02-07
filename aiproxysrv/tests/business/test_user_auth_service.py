"""
Unit tests for UserAuthService

Tests pure authentication logic WITHOUT database dependencies
- Password hashing and verification
- JWT token generation and validation
- Password strength validation
"""

import time
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from business.user_auth_service import UserAuthService
from config.settings import JWT_ALGORITHM, JWT_SECRET_KEY


class TestUserAuthService:
    """Test suite for UserAuthService (pure functions, no DB needed)"""

    @pytest.fixture
    def auth_service(self):
        """Create UserAuthService instance"""
        return UserAuthService()

    # ============================================
    # Password Hashing Tests
    # ============================================

    def test_hash_password_returns_string(self, auth_service):
        """Test that password hashing returns a string"""
        password = "mypassword123"
        hashed = auth_service.hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_creates_different_hashes(self, auth_service):
        """Test that same password creates different hashes (salt randomness)"""
        password = "mypassword123"
        hash1 = auth_service.hash_password(password)
        hash2 = auth_service.hash_password(password)

        # Different salts should create different hashes
        assert hash1 != hash2

    def test_hash_password_handles_special_characters(self, auth_service):
        """Test password hashing with special characters"""
        password = "p@ssw0rd!#$%^&*()"
        hashed = auth_service.hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0

    # ============================================
    # Password Verification Tests
    # ============================================

    def test_verify_password_correct(self, auth_service):
        """Test password verification with correct password"""
        password = "mypassword123"
        hashed = auth_service.hash_password(password)

        assert auth_service.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self, auth_service):
        """Test password verification with incorrect password"""
        password = "mypassword123"
        wrong_password = "wrongpassword"
        hashed = auth_service.hash_password(password)

        assert auth_service.verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_string(self, auth_service):
        """Test password verification with empty string"""
        password = "mypassword123"
        hashed = auth_service.hash_password(password)

        assert auth_service.verify_password("", hashed) is False

    def test_verify_password_case_sensitive(self, auth_service):
        """Test that password verification is case-sensitive"""
        password = "MyPassword123"
        wrong_case = "mypassword123"
        hashed = auth_service.hash_password(password)

        assert auth_service.verify_password(wrong_case, hashed) is False

    def test_verify_password_handles_invalid_hash(self, auth_service):
        """Test password verification with invalid hash"""
        password = "mypassword123"
        invalid_hash = "not_a_valid_hash"

        assert auth_service.verify_password(password, invalid_hash) is False

    # ============================================
    # JWT Token Generation Tests
    # ============================================

    def test_generate_jwt_token_returns_string(self, auth_service):
        """Test that JWT generation returns a string"""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        email = "test@example.com"

        token = auth_service.generate_jwt_token(user_id, email)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_jwt_token_contains_correct_payload(self, auth_service):
        """Test that JWT token contains correct user information"""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        email = "test@example.com"

        token = auth_service.generate_jwt_token(user_id, email)

        # Decode without verification to check payload
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        assert payload["user_id"] == user_id
        assert payload["email"] == email
        assert "iat" in payload  # Issued at
        assert "exp" in payload  # Expiration

    def test_generate_jwt_token_has_correct_expiration(self, auth_service):
        """Test that JWT token has correct expiration time"""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        email = "test@example.com"

        token = auth_service.generate_jwt_token(user_id, email)

        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        # Check expiration is in the future
        exp_timestamp = payload["exp"]
        iat_timestamp = payload["iat"]

        # Calculate expected expiration (should be jwt_expiration_hours from iat)
        expected_exp = iat_timestamp + (auth_service.jwt_expiration_hours * 3600)

        # Allow 2 second tolerance for test execution time
        assert abs(exp_timestamp - expected_exp) < 2

    def test_generate_jwt_token_creates_different_tokens(self, auth_service):
        """Test that same user gets different tokens (due to iat timestamp)"""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        email = "test@example.com"

        token1 = auth_service.generate_jwt_token(user_id, email)
        time.sleep(1)  # Wait 1 second to ensure different iat
        token2 = auth_service.generate_jwt_token(user_id, email)

        assert token1 != token2

    # ============================================
    # JWT Token Verification Tests
    # ============================================

    def test_verify_jwt_token_valid(self, auth_service):
        """Test JWT token verification with valid token"""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        email = "test@example.com"

        token = auth_service.generate_jwt_token(user_id, email)
        payload = auth_service.verify_jwt_token(token)

        assert payload is not None
        assert payload["user_id"] == user_id
        assert payload["email"] == email

    def test_verify_jwt_token_invalid_signature(self, auth_service):
        """Test JWT token verification with tampered token"""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        email = "test@example.com"

        token = auth_service.generate_jwt_token(user_id, email)

        # Tamper with token by modifying the signature part (after last dot)
        parts = token.split(".")
        if len(parts) == 3:
            # Change a character in the middle of the signature (not at the end)
            signature = parts[2]
            if len(signature) > 10:
                tampered_signature = signature[:5] + ("X" if signature[5] != "X" else "Y") + signature[6:]
                tampered_token = f"{parts[0]}.{parts[1]}.{tampered_signature}"
            else:
                # Fallback: append extra character
                tampered_token = token + "X"
        else:
            # Fallback: append extra character
            tampered_token = token + "X"

        payload = auth_service.verify_jwt_token(tampered_token)

        assert payload is None

    def test_verify_jwt_token_expired(self, auth_service):
        """Test JWT token verification with expired token"""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        email = "test@example.com"

        # Create token with immediate expiration
        payload = {
            "user_id": user_id,
            "email": email,
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC) - timedelta(hours=1),  # Expired 1 hour ago
        }
        expired_token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        result = auth_service.verify_jwt_token(expired_token)

        assert result is None

    def test_verify_jwt_token_malformed(self, auth_service):
        """Test JWT token verification with malformed token"""
        malformed_token = "not.a.valid.jwt.token"

        payload = auth_service.verify_jwt_token(malformed_token)

        assert payload is None

    def test_verify_jwt_token_empty_string(self, auth_service):
        """Test JWT token verification with empty string"""
        payload = auth_service.verify_jwt_token("")

        assert payload is None

    # ============================================
    # Password Strength Validation Tests
    # ============================================

    def test_validate_password_strength_valid(self, auth_service):
        """Test password strength validation with valid password"""
        password = "mypassword123"

        is_valid, error_msg = auth_service.validate_password_strength(password)

        assert is_valid is True
        assert error_msg is None

    def test_validate_password_strength_too_short(self, auth_service):
        """Test password strength validation with short password"""
        password = "short"

        is_valid, error_msg = auth_service.validate_password_strength(password)

        assert is_valid is False
        assert error_msg == "Password must be at least 8 characters long"

    def test_validate_password_strength_empty(self, auth_service):
        """Test password strength validation with empty password"""
        password = ""

        is_valid, error_msg = auth_service.validate_password_strength(password)

        assert is_valid is False
        assert error_msg == "Password cannot be empty"

    def test_validate_password_strength_exactly_8_chars(self, auth_service):
        """Test password strength validation with exactly 8 characters"""
        password = "password"

        is_valid, error_msg = auth_service.validate_password_strength(password)

        assert is_valid is True
        assert error_msg is None

    def test_validate_password_strength_special_characters(self, auth_service):
        """Test password strength validation with special characters"""
        password = "p@ssw0rd!#$"

        is_valid, error_msg = auth_service.validate_password_strength(password)

        assert is_valid is True
        assert error_msg is None

    # ============================================
    # Integration Tests (multiple methods)
    # ============================================

    def test_full_authentication_flow(self, auth_service):
        """Test complete authentication flow: hash, verify, generate token, verify token"""
        # 1. Hash password
        password = "mypassword123"
        hashed = auth_service.hash_password(password)

        # 2. Verify password
        assert auth_service.verify_password(password, hashed) is True

        # 3. Generate JWT token
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        email = "test@example.com"
        token = auth_service.generate_jwt_token(user_id, email)

        # 4. Verify JWT token
        payload = auth_service.verify_jwt_token(token)
        assert payload is not None
        assert payload["user_id"] == user_id
        assert payload["email"] == email

    def test_password_change_flow(self, auth_service):
        """Test password change flow: verify old, validate new, hash new"""
        # Old password
        old_password = "oldpassword123"
        old_hash = auth_service.hash_password(old_password)

        # 1. Verify old password
        assert auth_service.verify_password(old_password, old_hash) is True

        # 2. Validate new password strength
        new_password = "newpassword456"
        is_valid, error_msg = auth_service.validate_password_strength(new_password)
        assert is_valid is True

        # 3. Hash new password
        new_hash = auth_service.hash_password(new_password)

        # 4. Verify new password works
        assert auth_service.verify_password(new_password, new_hash) is True

        # 5. Old password should not work with new hash
        assert auth_service.verify_password(old_password, new_hash) is False
