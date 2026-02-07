"""OpenAI API Client - HTTP client for OpenAI API requests (Infrastructure layer)."""

from typing import Any

import requests

from config.settings import CHAT_DEBUG_LOGGING, OPENAI_ADMIN_BASE_URL, OPENAI_API_KEY, OPENAI_TIMEOUT
from utils.logger import logger


class OpenAIAPIClient:
    """HTTP client for OpenAI API."""

    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.base_url = OPENAI_ADMIN_BASE_URL
        self.timeout = OPENAI_TIMEOUT

    def chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Send chat completion request to OpenAI API.

        Args:
            payload: Request payload with model, messages, temperature, etc.

        Returns:
            OpenAI API response JSON

        Raises:
            OpenAIAPIError: If API call fails
        """
        if not self.api_key:
            raise OpenAIAPIError("OpenAI API key not configured")

        # Build API URL
        api_url = f"{self.base_url}/chat/completions"

        # Set headers with API key
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        # Conditional logging based on CHAT_DEBUG_LOGGING
        if CHAT_DEBUG_LOGGING:
            logger.debug(
                "OpenAI Chat API Request",
                url=api_url,
                model=payload.get("model"),
                temperature=payload.get("temperature", "default"),
                max_tokens=payload.get("max_tokens", "unlimited"),
                message_count=len(payload.get("messages", [])),
                messages=payload.get("messages"),
                full_payload=payload,
            )
        else:
            logger.info(
                "OpenAI Chat request", model=payload.get("model"), message_count=len(payload.get("messages", []))
            )

        try:
            resp = requests.post(api_url, headers=headers, json=payload, timeout=self.timeout)

            # Log response status
            if CHAT_DEBUG_LOGGING:
                logger.debug("OpenAI API Response received", status_code=resp.status_code)

            # Check for HTTP errors
            if resp.status_code != 200:
                error_body = resp.text
                logger.error(
                    "OpenAI API HTTP Error",
                    status_code=resp.status_code,
                    response_body=error_body[:500],  # First 500 chars
                )
                raise OpenAIAPIError(f"HTTP {resp.status_code}: {error_body[:200]}")

            resp_json = resp.json()

            # Debug: Log complete response details
            if CHAT_DEBUG_LOGGING:
                logger.debug(
                    "OpenAI Chat API Response",
                    response_model=resp_json.get("model"),
                    choice_count=len(resp_json.get("choices", [])),
                    usage=resp_json.get("usage"),
                    full_response=resp_json,
                )

            return resp_json

        except requests.exceptions.RequestException as e:
            logger.error("OpenAI API Network Error", error=str(e), error_type=type(e).__name__)
            raise OpenAIAPIError(f"Network Error: {e}")
        except Exception as e:
            logger.error(
                "Unexpected OpenAI API error",
                error_type=type(e).__name__,
                error=str(e),
            )
            raise OpenAIAPIError(f"Unexpected Error: {e}")


class OpenAIAPIError(Exception):
    """Custom exception for OpenAI API errors."""

    pass
