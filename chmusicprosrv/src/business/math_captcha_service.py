"""
Math CAPTCHA service (Business Layer)

Generates simple math challenges and verifies answers using JWT-signed tokens.
No external dependencies (replaces Google reCAPTCHA).
"""

import random
import time

import jwt

from config.settings import JWT_SECRET_KEY
from utils.logger import logger


CAPTCHA_EXPIRY_SECONDS = 300  # 5 minutes


class MathCaptchaService:
    """Stateless math CAPTCHA using JWT-signed challenge tokens"""

    def generate_challenge(self) -> tuple[str, str]:
        """
        Generate a math challenge with a signed token.

        Returns:
            Tuple of (question_text, signed_token)
        """
        op = random.choice(["add", "sub", "mul"])

        if op == "add":
            a, b = random.randint(2, 20), random.randint(2, 20)
            question = f"{a} + {b}"
            answer = a + b
        elif op == "sub":
            a = random.randint(5, 25)
            b = random.randint(1, a - 1)
            question = f"{a} - {b}"
            answer = a - b
        else:
            a, b = random.randint(2, 9), random.randint(2, 9)
            question = f"{a} x {b}"
            answer = a * b

        payload = {
            "answer": answer,
            "exp": int(time.time()) + CAPTCHA_EXPIRY_SECONDS,
            "type": "captcha",
        }
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")

        logger.debug("Math CAPTCHA generated", question=question)
        return question, token

    def verify_answer(self, token: str, user_answer: str) -> tuple[bool, str | None]:
        """
        Verify user's answer against the signed token.

        Args:
            token: The JWT-signed challenge token
            user_answer: The user's answer as string

        Returns:
            Tuple of (success, error_message)
        """
        if not token or not user_answer:
            return False, "CAPTCHA token and answer are required"

        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])

            if payload.get("type") != "captcha":
                return False, "Invalid CAPTCHA token"

            expected = str(payload["answer"])
            if user_answer.strip() == expected:
                logger.debug("Math CAPTCHA verified successfully")
                return True, None

            logger.debug("Math CAPTCHA wrong answer", expected=expected, got=user_answer.strip())
            return False, "Wrong answer"

        except jwt.ExpiredSignatureError:
            logger.debug("Math CAPTCHA token expired")
            return False, "CAPTCHA expired, please get a new one"
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid CAPTCHA token", error=str(e))
            return False, "Invalid CAPTCHA token"
