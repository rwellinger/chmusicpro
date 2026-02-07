"""Ollama API Client - HTTP client for Ollama API requests (Infrastructure layer)."""

import traceback
from typing import Any

import requests

from config.settings import CHAT_DEBUG_LOGGING, OLLAMA_TIMEOUT, OLLAMA_URL
from utils.logger import logger


class OllamaAPIClient:
    """HTTP client for Ollama API."""

    def __init__(self):
        self.base_url = OLLAMA_URL
        self.timeout = OLLAMA_TIMEOUT

    def generate(self, model: str, prompt: str, temperature: float, max_tokens: int | None) -> dict[str, Any]:
        """
        Send generation request to Ollama API.

        Args:
            model: Ollama model name (e.g., "llama3.2:3b")
            prompt: Prompt text to generate from
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate (None or <=0 means no limit)

        Returns:
            Ollama API response JSON

        Raises:
            OllamaAPIError: If API call fails
        """
        api_url = f"{self.base_url}/api/generate"
        headers = {"Content-Type": "application/json"}

        # Build options - only include num_predict if max_tokens is set and > 0
        options = {"temperature": temperature}
        if max_tokens is not None and max_tokens > 0:
            options["num_predict"] = max_tokens

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": options,
        }

        # Conditional logging based on CHAT_DEBUG_LOGGING
        if CHAT_DEBUG_LOGGING:
            logger.debug("Ollama API Request Details", api_url=api_url, full_payload=payload)
        else:
            logger.debug("Calling Ollama API", api_url=api_url, model=model)

        try:
            resp = requests.post(api_url, headers=headers, json=payload, timeout=self.timeout)

            if CHAT_DEBUG_LOGGING:
                logger.debug("Ollama API response received", status_code=resp.status_code)

            resp.raise_for_status()

        except requests.exceptions.Timeout:
            logger.error("Ollama API timeout", url=self.base_url)
            raise OllamaAPIError("Ollama API timeout")

        except requests.exceptions.ConnectionError:
            logger.error("Ollama API connection failed", url=self.base_url)
            raise OllamaAPIError("Cannot connect to Ollama API")

        except requests.exceptions.RequestException as e:
            logger.error(
                "Ollama API Network Error", error_type=type(e).__name__, error=str(e), stacktrace=traceback.format_exc()
            )
            raise OllamaAPIError(f"Network Error: {e}")

        except Exception as e:
            logger.error(
                "Unexpected Ollama API error",
                error_type=type(e).__name__,
                error=str(e),
                stacktrace=traceback.format_exc(),
            )
            raise OllamaAPIError(f"Unexpected Error: {e}")

        # Check HTTP status
        if resp.status_code != 200:
            logger.error("Ollama API Error Response", status_code=resp.status_code, response_text=resp.text)
            try:
                error_data = resp.json()
                raise OllamaAPIError(error_data)
            except ValueError:
                raise OllamaAPIError(f"HTTP {resp.status_code}: {resp.text}")

        # Parse response
        try:
            resp_json = resp.json()

            if CHAT_DEBUG_LOGGING:
                logger.debug("Ollama API raw response parsed", response_keys=list(resp_json.keys()))

            return resp_json
        except ValueError as e:
            logger.error(
                "Error parsing Ollama API response",
                error=str(e),
                response_text=resp.text,
                stacktrace=traceback.format_exc(),
            )
            raise OllamaAPIError(f"Invalid API response format: {e}")

    def get_tags(self) -> dict[str, Any]:
        """
        Get available Ollama models from server.

        Returns:
            Ollama API response JSON with models list

        Raises:
            OllamaAPIError: If API call fails
        """
        api_url = f"{self.base_url}/api/tags"
        logger.debug("Fetching Ollama models", api_url=api_url)

        try:
            response = requests.get(api_url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            logger.info("Ollama models fetched successfully", model_count=len(data.get("models", [])))

            return data

        except requests.exceptions.Timeout:
            logger.error("Ollama API timeout", url=self.base_url)
            raise OllamaAPIError("Ollama API timeout")

        except requests.exceptions.ConnectionError:
            logger.error("Ollama API connection failed", url=self.base_url)
            raise OllamaAPIError("Cannot connect to Ollama API")

        except requests.exceptions.RequestException as e:
            logger.error("Ollama API request failed", error=str(e), error_type=type(e).__name__)
            raise OllamaAPIError(f"Ollama API error: {str(e)}")

        except Exception as e:
            logger.error("Unexpected error in get_tags", error=str(e), error_type=type(e).__name__)
            raise OllamaAPIError(f"Unexpected error: {str(e)}")


class OllamaAPIError(Exception):
    """Custom exception for Ollama API errors."""

    pass
