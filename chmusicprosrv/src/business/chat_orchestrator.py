"""Chat Orchestrator - Coordinates Ollama chat operations (NOT testable, orchestration only)."""

import traceback
from typing import Any

from adapters.ollama.api_client import OllamaAPIClient, OllamaAPIError
from config.settings import CHAT_DEBUG_LOGGING
from utils.logger import logger


class ChatOrchestrator:
    """Orchestrator for Ollama chat operations (coordinates services, NO business logic)."""

    def __init__(self):
        self.api_client = OllamaAPIClient()

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

        Orchestrates: OllamaAPIClient + prompt structuring

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
        # Validate input
        if not model or not prompt:
            return {"error": "Missing model or prompt"}, 400

        # Build full prompt optimized for gpt-oss:20b with clear instruction separation
        # Structure: [INSTRUCTION] pre_condition [USER] prompt [ADDITIONAL] user_instructions [FORMAT] post_condition
        user_part = f" [ADDITIONAL] {user_instructions}" if user_instructions.strip() else ""
        full_prompt = f"[INSTRUCTION] {pre_condition or ''} [USER] {prompt}{user_part} [FORMAT] {post_condition or ''}"

        try:
            # Conditional logging based on CHAT_DEBUG_LOGGING
            if CHAT_DEBUG_LOGGING:
                logger.debug(
                    "Ollama Chat Request",
                    category=category,
                    action=action,
                    model=model,
                    pre_condition=pre_condition,
                    prompt=prompt,
                    user_instructions=user_instructions,
                    post_condition=post_condition,
                    full_prompt=full_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            else:
                logger.info(
                    "Ollama chat request", category=category, action=action, model=model, prompt_length=len(prompt)
                )

            # Call API client
            response_data = self.api_client.generate(model, full_prompt, temperature, max_tokens)

            # Clean response (remove context)
            cleaned_response = self._clean_ollama_response(response_data)

            # Build template identifier for logging
            template_id = f"{category}/{action}" if category and action else "unknown"

            # Log warning if response is empty (token limit exceeded by thinking, etc.)
            if not cleaned_response.get("response", "").strip():
                eval_count = cleaned_response.get("eval_count", 0)
                done_reason = cleaned_response.get("done_reason", "")

                # Definitively token limit reached
                if eval_count >= max_tokens and done_reason == "length":
                    logger.warning(
                        "Empty response: Token limit reached exactly (likely consumed by thinking/reasoning)",
                        template=template_id,
                        category=category,
                        action=action,
                        model=model,
                        eval_count=eval_count,
                        max_tokens=max_tokens,
                        done_reason=done_reason,
                    )
                else:
                    # Unknown cause
                    logger.warning(
                        "Empty response: Unknown cause",
                        template=template_id,
                        category=category,
                        action=action,
                        model=model,
                        eval_count=eval_count,
                        max_tokens=max_tokens,
                        done_reason=done_reason,
                    )

            if CHAT_DEBUG_LOGGING:
                logger.debug(
                    "Ollama Chat Response",
                    category=category,
                    action=action,
                    model=model,
                    response_data=cleaned_response,
                )
            else:
                logger.info("Ollama chat completed", category=category, action=action, model=model)

            return cleaned_response, 200

        except OllamaAPIError as e:
            logger.error(
                "Ollama API Error during chat generation",
                category=category,
                action=action,
                model=model,
                error=str(e),
                stacktrace=traceback.format_exc(),
            )
            return {"error": f"Ollama API Error: {e}"}, 500
        except Exception as e:
            logger.error(
                "Unexpected error in chat generation",
                category=category,
                action=action,
                model=model,
                error_type=type(e).__name__,
                error=str(e),
                stacktrace=traceback.format_exc(),
            )
            return {"error": f"Unexpected Error: {e}"}, 500

    def _clean_ollama_response(self, response_data: dict[str, Any]) -> dict[str, Any]:
        """Clean Ollama response by removing context field (post-processing)."""
        cleaned = response_data.copy()

        # Remove context field if present
        if "context" in cleaned:
            del cleaned["context"]

        return cleaned
