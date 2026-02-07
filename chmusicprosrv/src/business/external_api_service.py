"""External API Service - Handles third-party API integrations"""

import requests

from config.settings import (
    CHAT_DEBUG_LOGGING,
    OPENAI_ADMIN_BASE_URL,
    OPENAI_API_KEY,
    OPENAI_IMAGE_MODEL,
    OPENAI_TIMEOUT,
)
from utils.logger import logger


class OpenAIAPIError(Exception):
    """Custom exception for OpenAI API errors"""

    pass


class OpenAIService:
    """Service for OpenAI API integration (Images)"""

    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.base_url = OPENAI_ADMIN_BASE_URL
        self.model = OPENAI_IMAGE_MODEL

    def generate_image(self, prompt: str, size: str) -> str:
        """
        Generate image using OpenAI DALL-E API

        Args:
            prompt: Image generation prompt
            size: Image size specification

        Returns:
            URL of the generated image

        Raises:
            OpenAIAPIError: If API call fails
        """
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        payload = {"model": self.model, "prompt": prompt, "size": size, "n": 1}

        api_url = f"{self.base_url}/images/generations"

        # Conditional logging based on CHAT_DEBUG_LOGGING
        if CHAT_DEBUG_LOGGING:
            logger.debug(
                "OpenAI Image API Request",
                api_url=api_url,
                model=self.model,
                prompt=prompt,
                size=size,
                full_payload=payload,
            )
        else:
            logger.info("OpenAI image request", model=self.model, size=size, prompt_length=len(prompt))

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
            image_url = response_json["data"][0]["url"]

            if CHAT_DEBUG_LOGGING:
                logger.debug(
                    "OpenAI Image API Response Details",
                    image_url=image_url,
                    response_data_count=len(response_json.get("data", [])),
                    full_response=response_json,
                )
            else:
                logger.info("OpenAI image generated", url_received=True)

            return image_url

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
