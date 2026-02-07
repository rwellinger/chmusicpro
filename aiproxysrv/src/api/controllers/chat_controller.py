"""Chat Controller - HTTP request/response handling for Chat operations (Controller layer)."""

from typing import Any

from business.chat_orchestrator import ChatOrchestrator


class ChatController:
    """Controller for chat generation (HTTP handling only, delegates to orchestrator)."""

    def __init__(self):
        self.orchestrator = ChatOrchestrator()

    def generate_chat(
        self,
        model: str,
        pre_condition: str,
        prompt: str,
        post_condition: str,
        temperature: float = 0.3,
        max_tokens: int | None = None,
        user_instructions: str = "",
        category: str | None = None,
        action: str | None = None,
    ) -> tuple[dict[str, Any], int]:
        """
        Generate chat response with Ollama.

        Args:
            model: Ollama model to use (e.g. "llama3.2:3b")
            pre_condition: Text to prepend to prompt
            prompt: Main prompt text
            post_condition: Text to append to prompt
            temperature: Sampling temperature (default 0.3)
            max_tokens: Maximum tokens to generate (None or <=0 means no limit, let model decide)
            user_instructions: Optional user-specific instructions (placed between prompt and post_condition)
            category: Template category for logging (optional)
            action: Template action for logging (optional)

        Returns:
            Tuple of (response_data, status_code)
        """
        return self.orchestrator.generate_chat(
            model, pre_condition, prompt, post_condition, temperature, max_tokens, user_instructions, category, action
        )
