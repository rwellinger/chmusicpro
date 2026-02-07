"""OpenAI Chat Controller - HTTP request/response handling for OpenAI Chat API (Controller layer)."""

from typing import Any

from adapters.openai.api_client import OpenAIAPIError  # noqa: F401 # Re-export for backward compatibility
from business.openai_chat_orchestrator import OpenAIChatOrchestrator


__all__ = ["OpenAIChatController", "OpenAIAPIError"]


class OpenAIChatController:
    """Controller for OpenAI Chat API integration (HTTP handling only, delegates to orchestrator)."""

    def __init__(self):
        self.orchestrator = OpenAIChatOrchestrator()

    def send_chat_message(
        self, model: str, messages: list[dict[str, str]], temperature: float = 0.7, max_tokens: int | None = None
    ) -> tuple[str, int, int]:
        """
        Send chat message to OpenAI API.

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
        return self.orchestrator.send_chat_message(model, messages, temperature, max_tokens)

    def get_available_models(self) -> list[dict[str, Any]]:
        """
        Get list of available OpenAI Chat models from configuration.

        Returns:
            List of model dictionaries with name and context_window
        """
        return self.orchestrator.get_available_models()
