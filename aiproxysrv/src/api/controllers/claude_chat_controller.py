"""Claude Chat Controller - HTTP request/response handling for Claude Messages API (Controller layer)."""

from typing import Any

from adapters.claude.api_client import ClaudeAPIError  # noqa: F401 # Re-export for backward compatibility
from business.claude_chat_orchestrator import ClaudeChatOrchestrator


__all__ = ["ClaudeChatController", "ClaudeAPIError"]


class ClaudeChatController:
    """Controller for Claude Messages API integration (HTTP handling only, delegates to orchestrator)."""

    def __init__(self):
        self.orchestrator = ClaudeChatOrchestrator()

    def send_chat_message(
        self, model: str, messages: list[dict[str, str]], max_tokens: int, temperature: float = 0.7
    ) -> tuple[str, int, int]:
        """
        Send chat message to Claude Messages API.

        Args:
            model: Claude model name (e.g., "claude-sonnet-4-5-20250929")
            messages: List of messages with role and content
            max_tokens: Maximum tokens to generate (REQUIRED by Claude)
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            Tuple of (assistant_content, input_tokens, output_tokens)

        Raises:
            ClaudeAPIError: If API call fails
        """
        return self.orchestrator.send_chat_message(model, messages, max_tokens, temperature)

    def get_available_models(self) -> list[dict[str, Any]]:
        """
        Get list of available Claude Chat models from configuration.

        Returns:
            List of model dictionaries with name and context_window
        """
        return self.orchestrator.get_available_models()
