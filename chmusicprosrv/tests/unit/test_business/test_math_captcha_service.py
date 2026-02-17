"""Unit tests for MathCaptchaService"""

import time

import jwt
import pytest

from business.math_captcha_service import CAPTCHA_EXPIRY_SECONDS, MathCaptchaService


@pytest.mark.unit
class TestMathCaptchaService:
    """Test MathCaptchaService challenge generation and verification"""

    def setup_method(self):
        self.service = MathCaptchaService()

    def test_generate_challenge_returns_question_and_token(self):
        """Generate returns a non-empty question and JWT token"""
        question, token = self.service.generate_challenge()

        assert question
        assert token
        assert "=" not in question  # Question should be like "7 + 3", not "7 + 3 = ?"

    def test_generate_challenge_token_is_valid_jwt(self, mocker):
        """Token contains answer, expiry, and type=captcha"""
        mocker.patch("business.math_captcha_service.JWT_SECRET_KEY", "test-secret")
        question, token = self.service.generate_challenge()

        payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
        assert "answer" in payload
        assert payload["type"] == "captcha"
        assert payload["exp"] > time.time()
        assert payload["exp"] <= time.time() + CAPTCHA_EXPIRY_SECONDS + 1

    def test_verify_correct_answer(self, mocker):
        """Correct answer returns (True, None)"""
        mocker.patch("business.math_captcha_service.JWT_SECRET_KEY", "test-secret")
        question, token = self.service.generate_challenge()

        # Decode to get the expected answer
        payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
        answer = str(payload["answer"])

        success, error = self.service.verify_answer(token, answer)
        assert success is True
        assert error is None

    def test_verify_wrong_answer(self, mocker):
        """Wrong answer returns (False, 'Wrong answer')"""
        mocker.patch("business.math_captcha_service.JWT_SECRET_KEY", "test-secret")
        _question, token = self.service.generate_challenge()

        success, error = self.service.verify_answer(token, "99999")
        assert success is False
        assert error == "Wrong answer"

    def test_verify_expired_token(self, mocker):
        """Expired token returns appropriate error"""
        mocker.patch("business.math_captcha_service.JWT_SECRET_KEY", "test-secret")

        # Create an already-expired token
        payload = {"answer": 10, "exp": int(time.time()) - 10, "type": "captcha"}
        expired_token = jwt.encode(payload, "test-secret", algorithm="HS256")

        success, error = self.service.verify_answer(expired_token, "10")
        assert success is False
        assert "expired" in error.lower()

    def test_verify_invalid_token(self, mocker):
        """Invalid/tampered token returns error"""
        mocker.patch("business.math_captcha_service.JWT_SECRET_KEY", "test-secret")

        success, error = self.service.verify_answer("not-a-valid-token", "10")
        assert success is False
        assert "Invalid" in error

    def test_verify_empty_inputs(self):
        """Empty token or answer returns error"""
        success, error = self.service.verify_answer("", "10")
        assert success is False

        success, error = self.service.verify_answer("some-token", "")
        assert success is False

    def test_verify_answer_with_whitespace(self, mocker):
        """Answer with leading/trailing spaces is accepted"""
        mocker.patch("business.math_captcha_service.JWT_SECRET_KEY", "test-secret")
        _question, token = self.service.generate_challenge()

        payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
        answer = str(payload["answer"])

        success, error = self.service.verify_answer(token, f"  {answer}  ")
        assert success is True
        assert error is None

    def test_generate_produces_varied_operations(self, mocker):
        """Multiple calls should produce different operation types"""
        mocker.patch("business.math_captcha_service.JWT_SECRET_KEY", "test-secret")
        operations = set()
        for _ in range(50):
            question, _ = self.service.generate_challenge()
            if "+" in question:
                operations.add("add")
            elif "-" in question:
                operations.add("sub")
            elif "x" in question:
                operations.add("mul")

        assert len(operations) >= 2  # At least 2 different operations in 50 tries
