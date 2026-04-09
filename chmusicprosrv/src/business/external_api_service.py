"""External API Service - Handles third-party API integrations"""

import base64

import requests

from config.settings import (
    CHAT_DEBUG_LOGGING,
    OPENAI_ADMIN_BASE_URL,
    OPENAI_IMAGE_MODEL,
    OPENAI_IMAGE_QUALITY,
    OPENAI_TIMEOUT,
)
from utils.logger import logger


class OpenAIAPIError(Exception):
    """Custom exception for OpenAI API errors"""

    pass


class OpenAIService:
    """Service for OpenAI API integration (Images)"""

    def __init__(self):
        self.base_url = OPENAI_ADMIN_BASE_URL
        self.model = OPENAI_IMAGE_MODEL
        self.quality = OPENAI_IMAGE_QUALITY

    @property
    def api_key(self) -> str | None:
        """Resolve API key: per-user key from flask.g (no fallback to .env)."""
        try:
            from flask import g

            return getattr(g, "user_openai_api_key", None)
        except RuntimeError:
            return None

    def generate_image(self, prompt: str, size: str) -> bytes:
        """
        Generate image using OpenAI Image API (gpt-image-1)

        Args:
            prompt: Image generation prompt
            size: Image size specification

        Returns:
            Raw image bytes (PNG)

        Raises:
            OpenAIAPIError: If API call fails
        """
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        payload = {
            "model": self.model,
            "prompt": prompt,
            "size": size,
            "n": 1,
            "quality": self.quality,
        }

        api_url = f"{self.base_url}/images/generations"

        # Conditional logging based on CHAT_DEBUG_LOGGING
        if CHAT_DEBUG_LOGGING:
            logger.debug(
                "OpenAI Image API Request",
                api_url=api_url,
                model=self.model,
                prompt=prompt,
                size=size,
                quality=self.quality,
                full_payload=payload,
            )
        else:
            logger.info(
                "OpenAI image request", model=self.model, size=size, quality=self.quality, prompt_length=len(prompt)
            )

        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=OPENAI_TIMEOUT)

            if CHAT_DEBUG_LOGGING:
                logger.debug("OpenAI Image API response received", status_code=response.status_code)
            else:
                logger.info("OpenAI image response", status_code=response.status_code)

            response.raise_for_status()

        except requests.exceptions.RequestException as e:
            logger.error("OpenAI Image API Network Error", error_type=type(e).__name__, error=str(e))
            raise OpenAIAPIError(f"Network Error: {e}") from e
        except Exception as e:
            logger.error("Unexpected OpenAI Image API error", error_type=type(e).__name__, error=str(e))
            raise OpenAIAPIError(f"API Error: {e}") from e

        if response.status_code != 200:
            logger.error(
                "OpenAI Image API Error Response", status_code=response.status_code, response_text=response.text
            )
            try:
                error_data = response.json()
                raise OpenAIAPIError(f"API Error: {error_data}")
            except ValueError:
                raise OpenAIAPIError(f"HTTP {response.status_code}: {response.text}")

        try:
            response_json = response.json()
            b64_data = response_json["data"][0]["b64_json"]
            image_bytes = base64.b64decode(b64_data)

            if CHAT_DEBUG_LOGGING:
                logger.debug(
                    "OpenAI Image API Response Details",
                    image_size_bytes=len(image_bytes),
                    response_data_count=len(response_json.get("data", [])),
                )
            else:
                logger.info("OpenAI image generated", image_size_bytes=len(image_bytes))

            return image_bytes

        except (KeyError, IndexError, ValueError) as e:
            logger.error("Error parsing OpenAI Image API response", error=str(e), response_text=response.text)
            raise OpenAIAPIError(f"Invalid API response format: {e}") from e

    def validate_api_key(self) -> bool:
        """
        Validate OpenAI API key

        Returns:
            True if API key is valid, False otherwise
        """
        if not self.api_key:
            return False

        # You could implement a simple API call to validate the key
        # For now, just check if it's not empty
        return bool(self.api_key.strip())
