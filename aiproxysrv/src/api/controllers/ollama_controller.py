"""Ollama Controller - HTTP request/response handling for Ollama API (Controller layer)."""

from typing import Any

from business.ollama_orchestrator import OllamaOrchestrator


class OllamaController:
    """Controller for Ollama API integration (HTTP handling only, delegates to orchestrator)."""

    def __init__(self):
        self.orchestrator = OllamaOrchestrator()

    def get_models(self) -> tuple[dict[str, Any], int]:
        """
        Get available Ollama models (raw response from server).

        Returns:
            Tuple of (response_data, status_code)
        """
        return self.orchestrator.get_models()

    def get_available_chat_models(self) -> tuple[dict[str, Any], int]:
        """
        Get available Ollama chat models based on configuration.

        Behavior (via orchestrator):
        - OLLAMA_CHAT_MODELS empty: Fetch all models from Ollama server
        - OLLAMA_CHAT_MODELS set: Return only whitelisted models (static)

        Returns:
            Tuple of (response_data, status_code)
            Response format: {"models": [{"name": str, "context_window": int, "is_default": bool}]}
        """
        return self.orchestrator.get_available_chat_models()
