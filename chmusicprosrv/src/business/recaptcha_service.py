"""
reCAPTCHA verification service (Business Layer)

Verifies Google reCAPTCHA v2 tokens against the Google API.
Skips verification when RECAPTCHA_SECRET_KEY is empty (development mode).
"""

import requests

from config.settings import RECAPTCHA_SECRET_KEY
from utils.logger import logger


RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"


class RecaptchaService:
    """Google reCAPTCHA v2 verification"""

    def verify_token(self, token: str, remote_ip: str = None) -> tuple[bool, str | None]:
        """
        Verify a reCAPTCHA token.

        Args:
            token: The reCAPTCHA response token from the client
            remote_ip: Optional client IP address

        Returns:
            Tuple of (success, error_message)
        """
        if not RECAPTCHA_SECRET_KEY:
            logger.debug("reCAPTCHA verification skipped (no secret key configured)")
            return True, None

        try:
            payload = {
                "secret": RECAPTCHA_SECRET_KEY,
                "response": token,
            }
            if remote_ip:
                payload["remoteip"] = remote_ip

            response = requests.post(RECAPTCHA_VERIFY_URL, data=payload, timeout=10)
            result = response.json()

            if result.get("success"):
                logger.debug("reCAPTCHA verification successful")
                return True, None

            error_codes = result.get("error-codes", [])
            error_msg = f"reCAPTCHA verification failed: {', '.join(error_codes)}"
            logger.warning(error_msg)
            return False, error_msg

        except requests.RequestException as e:
            error_msg = f"reCAPTCHA verification request failed: {e}"
            logger.error(error_msg)
            return False, error_msg
