"""Claude API Client - HTTP client for Anthropic Claude Messages API (Infrastructure layer)."""

from typing import Any

import requests

from config.settings import CHAT_DEBUG_LOGGING, CLAUDE_API_KEY, CLAUDE_API_VERSION, CLAUDE_BASE_URL, CLAUDE_TIMEOUT
from utils.logger import logger


class ClaudeAPIClient:
    """HTTP client for Claude Messages API."""

    def __init__(self):
        self.api_key = CLAUDE_API_KEY
        self.base_url = CLAUDE_BASE_URL
        self.api_version = CLAUDE_API_VERSION
        self.timeout = CLAUDE_TIMEOUT

    def messages_create(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Send messages request to Claude API.

        Args:
            payload: Request payload with model, messages, max_tokens, etc.

        Returns:
            Claude API response JSON

        Raises:
            ClaudeAPIError: If API call fails
        """
        if not self.api_key:
            raise ClaudeAPIError("Claude API key not configured")

        # Build API URL
        api_url = f"{self.base_url}/messages"

        # Set headers with API key and version
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
            "Content-Type": "application/json",
        }

        # Conditional logging based on CHAT_DEBUG_LOGGING
        if CHAT_DEBUG_LOGGING:
            logger.debug(
                "Claude Messages API Request",
                url=api_url,
                model=payload.get("model"),
                temperature=payload.get("temperature", "default"),
                max_tokens=payload.get("max_tokens"),
                message_count=len(payload.get("messages", [])),
                has_system=bool(payload.get("system")),
                messages=payload.get("messages"),
                full_payload=payload,
            )
        else:
            logger.info(
                "Claude Messages request", model=payload.get("model"), message_count=len(payload.get("messages", []))
            )

        try:
            resp = requests.post(api_url, headers=headers, json=payload, timeout=self.timeout)

            # Log response status
            if CHAT_DEBUG_LOGGING:
                logger.debug("Claude API Response received", status_code=resp.status_code)

            # Check for HTTP errors
            if resp.status_code != 200:
                error_body = resp.text
                logger.error(
                    "Claude API HTTP Error",
                    status_code=resp.status_code,
                    response_body=error_body[:500],  # First 500 chars
                )
                raise ClaudeAPIError(f"HTTP {resp.status_code}: {error_body[:200]}")

            resp_json = resp.json()

            # Debug: Log complete response details
            if CHAT_DEBUG_LOGGING:
                logger.debug(
                    "Claude Messages API Response",
                    response_id=resp_json.get("id"),
                    response_model=resp_json.get("model"),
                    stop_reason=resp_json.get("stop_reason"),
                    usage=resp_json.get("usage"),
                    full_response=resp_json,
                )

            return resp_json

        except requests.exceptions.RequestException as e:
            logger.error("Claude API Network Error", error=str(e), error_type=type(e).__name__)
            raise ClaudeAPIError(f"Network Error: {e}")
        except Exception as e:
            logger.error(
                "Unexpected Claude API error",
                error_type=type(e).__name__,
                error=str(e),
            )
            raise ClaudeAPIError(f"Unexpected Error: {e}")

    def get_models(self) -> dict[str, Any]:
        """
        Get available Claude models from Anthropic API.

        API Reference:
            GET https://api.anthropic.com/v1/models
            Headers: x-api-key, anthropic-version: 2023-06-01
            Response: {
                "data": [
                    {
                        "id": "claude-sonnet-4-5-20250929",
                        "created_at": "2025-01-15T12:00:00Z",
                        "display_name": "Claude Sonnet 4.5",
                        "type": "model"
                    }
                ],
                "has_more": false,
                "first_id": "...",
                "last_id": "..."
            }

        Returns:
            Anthropic API response JSON with models list

        Raises:
            ClaudeAPIError: If API call fails
        """
        if not self.api_key:
            raise ClaudeAPIError("Claude API key not configured")

        api_url = f"{self.base_url}/models"

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
        }

        if CHAT_DEBUG_LOGGING:
            logger.debug("Fetching Claude models from API", api_url=api_url)
        else:
            logger.info("Fetching Claude models")

        try:
            resp = requests.get(api_url, headers=headers, timeout=self.timeout)

            if CHAT_DEBUG_LOGGING:
                logger.debug("Claude Models API Response received", status_code=resp.status_code)

            # Check for HTTP errors
            if resp.status_code != 200:
                error_body = resp.text
                logger.error(
                    "Claude Models API HTTP Error",
                    status_code=resp.status_code,
                    response_body=error_body[:500],
                )
                raise ClaudeAPIError(f"HTTP {resp.status_code}: {error_body[:200]}")

            resp_json = resp.json()

            if CHAT_DEBUG_LOGGING:
                logger.debug(
                    "Claude Models API Response",
                    model_count=len(resp_json.get("data", [])),
                    has_more=resp_json.get("has_more", False),
                    full_response=resp_json,
                )

            return resp_json

        except requests.exceptions.Timeout:
            logger.error("Claude Models API timeout", url=self.base_url)
            raise ClaudeAPIError("Claude Models API timeout")

        except requests.exceptions.ConnectionError:
            logger.error("Claude Models API connection failed", url=self.base_url)
            raise ClaudeAPIError("Cannot connect to Claude Models API")

        except requests.exceptions.RequestException as e:
            logger.error("Claude Models API request failed", error=str(e), error_type=type(e).__name__)
            raise ClaudeAPIError(f"Claude Models API error: {str(e)}")

        except Exception as e:
            logger.error(
                "Unexpected error in get_models",
                error_type=type(e).__name__,
                error=str(e),
            )
            raise ClaudeAPIError(f"Unexpected error: {str(e)}")


class ClaudeAPIError(Exception):
    """Custom exception for Claude API errors."""

    pass
