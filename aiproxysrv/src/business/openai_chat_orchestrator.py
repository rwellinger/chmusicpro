"""OpenAI Chat Orchestrator - Coordinates OpenAI Chat API operations (NOT testable, orchestration only)."""

from typing import Any

from adapters.openai.api_client import OpenAIAPIClient
from business.openai_chat_transformer import build_chat_payload, get_available_models, parse_chat_response
from config.settings import CHAT_DEBUG_LOGGING, OPENAI_CHAT_MODELS
from utils.logger import logger


class OpenAIChatOrchestrator:
    """Orchestrator for OpenAI Chat API integration (coordinates services, NO business logic)."""

    def __init__(self):
        self.api_client = OpenAIAPIClient()

    def send_chat_message(
        self, model: str, messages: list[dict[str, str]], temperature: float = 0.7, max_tokens: int | None = None
    ) -> tuple[str, int, int]:
        """
        Send chat message to OpenAI API (orchestrates transformer + API client).

        Args:
            model: OpenAI model name (e.g., "gpt-4o")
            messages: List of messages with role and content
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate (optional)

        Returns:
            Tuple of (assistant_content, prompt_tokens, completion_tokens)

        Raises:
            OpenAIAPIError: If API call fails
        """
        # Build payload using transformer
        payload = build_chat_payload(model, messages, temperature, max_tokens)

        # Call API client
        resp_json = self.api_client.chat_completion(payload)

        # Parse response using transformer
        content, prompt_tokens, completion_tokens = parse_chat_response(resp_json)

        if CHAT_DEBUG_LOGGING:
            logger.debug(
                "Token counts extracted",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                content_length=len(content),
            )

        return content, prompt_tokens, completion_tokens

    def get_available_models(self) -> list[dict[str, Any]]:
        """
        Get list of available OpenAI Chat models from configuration.

        Returns:
            List of model dictionaries with name and context_window
        """
        # Use transformer to parse models config
        return get_available_models(OPENAI_CHAT_MODELS)
