"""Unit tests for RecaptchaService"""

import pytest
import requests

from business.recaptcha_service import RecaptchaService


@pytest.mark.unit
class TestRecaptchaService:
    """Test RecaptchaService.verify_token code paths"""

    def test_verify_skips_when_no_secret_key(self, mocker):
        """When RECAPTCHA_SECRET_KEY is empty, verification is skipped (dev mode)"""
        mocker.patch("business.recaptcha_service.RECAPTCHA_SECRET_KEY", "")

        service = RecaptchaService()
        success, error = service.verify_token("any-token")

        assert success is True
        assert error is None

    def test_verify_success(self, mocker, mock_requests_post):
        """Successful reCAPTCHA verification returns (True, None)"""
        mocker.patch("business.recaptcha_service.RECAPTCHA_SECRET_KEY", "test-secret")
        mock_requests_post.return_value.json.return_value = {"success": True}

        service = RecaptchaService()
        success, error = service.verify_token("valid-token")

        assert success is True
        assert error is None
        mock_requests_post.assert_called_once()

    def test_verify_failure_with_error_codes(self, mocker, mock_requests_post):
        """Failed reCAPTCHA verification returns error codes from Google"""
        mocker.patch("business.recaptcha_service.RECAPTCHA_SECRET_KEY", "test-secret")
        mock_requests_post.return_value.json.return_value = {
            "success": False,
            "error-codes": ["invalid-input-response", "timeout-or-duplicate"],
        }

        service = RecaptchaService()
        success, error = service.verify_token("bad-token")

        assert success is False
        assert "reCAPTCHA verification failed:" in error
        assert "invalid-input-response" in error
        assert "timeout-or-duplicate" in error

    def test_verify_handles_request_exception(self, mocker):
        """Network errors are caught and returned as error message"""
        mocker.patch("business.recaptcha_service.RECAPTCHA_SECRET_KEY", "test-secret")
        mocker.patch(
            "requests.post",
            side_effect=requests.ConnectionError("Connection refused"),
        )

        service = RecaptchaService()
        success, error = service.verify_token("some-token")

        assert success is False
        assert "reCAPTCHA verification request failed:" in error
        assert "Connection refused" in error

    def test_verify_includes_remote_ip_in_payload(self, mocker, mock_requests_post):
        """When remote_ip is provided, it is included in the POST payload"""
        mocker.patch("business.recaptcha_service.RECAPTCHA_SECRET_KEY", "test-secret")
        mock_requests_post.return_value.json.return_value = {"success": True}

        service = RecaptchaService()
        service.verify_token("some-token", remote_ip="192.168.1.1")

        call_kwargs = mock_requests_post.call_args
        payload = call_kwargs.kwargs["data"]
        assert payload["remoteip"] == "192.168.1.1"
        assert payload["secret"] == "test-secret"
        assert payload["response"] == "some-token"
