"""Chat Orchestrator - Coordinates AI chat operations across providers (NOT testable, orchestration only)."""

import traceback
from typing import Any

from business.ai_adapter import AIAdapterFactory, AIGenerationRequest
from config.ai_config import PROVIDER_OLLAMA
from config.settings import CHAT_DEBUG_LOGGING
from db.database import SessionLocal
from db.usage_log_service import UsageLogService
from utils.logger import logger


class ChatOrchestrator:
    """Orchestrator for AI chat operations (coordinates services, NO business logic)."""

    def __init__(self):
        self.usage_log_service = UsageLogService()

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
        user_id: str | None = None,
        provider: str = "ollama",
    ) -> tuple[dict[str, Any], int]:
        """
        Generate chat response via configured AI provider.

        Args:
            model: AI model to use (e.g. "llama3.2:3b", "gpt-4.1-mini", "claude-haiku-4-5-20250929")
            pre_condition: Text to prepend to prompt (system instructions)
            prompt: Main prompt text (user input)
            post_condition: Text to append to prompt (output format instructions)
            temperature: Sampling temperature (default 0.3)
            max_tokens: Maximum tokens to generate (None or <=0 means no limit, let model decide)
            user_instructions: Optional user-specific instructions (placed between prompt and post_condition)
            category: Template category for logging (optional)
            action: Template action for logging (optional)
            user_id: User ID for usage tracking (optional)
            provider: AI provider to use (ollama, openai, claude)

        Returns:
            Tuple of (response_data, status_code)
        """
        if not model or not prompt:
            return {"error": "Missing model or prompt"}, 400

        try:
            adapter = AIAdapterFactory.create_adapter(provider)
        except ValueError as e:
            logger.error("Failed to create AI adapter", provider=provider, error=str(e))
            return {"error": str(e)}, 400

        try:
            if provider == PROVIDER_OLLAMA:
                response_data, status_code = self._generate_ollama(
                    adapter,
                    model,
                    pre_condition,
                    prompt,
                    post_condition,
                    temperature,
                    max_tokens,
                    user_instructions,
                    category,
                    action,
                )
            else:
                response_data, status_code = self._generate_external(
                    adapter,
                    model,
                    pre_condition,
                    prompt,
                    post_condition,
                    temperature,
                    max_tokens,
                    user_instructions,
                    category,
                    action,
                    provider,
                )

            # Log usage for cost tracking (fire-and-forget, never block response)
            if user_id and status_code == 200:
                self._log_usage(user_id, model, category, action, response_data, provider)

            return response_data, status_code

        except Exception as e:
            logger.error(
                "Unexpected error in chat generation",
                category=category,
                action=action,
                model=model,
                provider=provider,
                error_type=type(e).__name__,
                error=str(e),
                stacktrace=traceback.format_exc(),
            )
            return {"error": f"AI Generation Error ({provider}): {e}"}, 500

    def _generate_ollama(
        self,
        adapter,
        model: str,
        pre_condition: str,
        prompt: str,
        post_condition: str,
        temperature: float,
        max_tokens: int | None,
        user_instructions: str,
        category: str | None,
        action: str | None,
    ) -> tuple[dict[str, Any], int]:
        """Generate via Ollama with single-string prompt format."""
        # Build full prompt optimized for gpt-oss:20b with clear instruction separation
        user_part = f" [ADDITIONAL] {user_instructions}" if user_instructions.strip() else ""
        full_prompt = f"[INSTRUCTION] {pre_condition or ''} [USER] {prompt}{user_part} [FORMAT] {post_condition or ''}"

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
                "Ollama chat request [{}/{}] model={}",
                category,
                action,
                model,
                prompt_length=len(prompt),
            )

        request = AIGenerationRequest(
            model=model,
            prompt=full_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        response = adapter.generate(request)

        # Build Ollama-compatible response dict (preserve existing response format)
        cleaned = response.raw_response.copy()
        if "context" in cleaned:
            del cleaned["context"]

        # Log warning if response is empty
        template_id = f"{category}/{action}" if category and action else "unknown"
        if not cleaned.get("response", "").strip():
            eval_count = cleaned.get("eval_count", 0)
            done_reason = cleaned.get("done_reason", "")
            if max_tokens and eval_count >= max_tokens and done_reason == "length":
                logger.warning(
                    "Empty response: Token limit reached exactly",
                    template=template_id,
                    model=model,
                    eval_count=eval_count,
                    max_tokens=max_tokens,
                )
            else:
                logger.warning(
                    "Empty response: Unknown cause",
                    template=template_id,
                    model=model,
                    eval_count=eval_count,
                    max_tokens=max_tokens,
                    done_reason=done_reason,
                )

        if CHAT_DEBUG_LOGGING:
            logger.debug("Ollama Chat Response", category=category, action=action, model=model, response_data=cleaned)
        else:
            logger.info("Ollama chat completed [{}/{}] model={}", category, action, model)

        return cleaned, 200

    def _generate_external(
        self,
        adapter,
        model: str,
        pre_condition: str,
        prompt: str,
        post_condition: str,
        temperature: float,
        max_tokens: int | None,
        user_instructions: str,
        category: str | None,
        action: str | None,
        provider: str,
    ) -> tuple[dict[str, Any], int]:
        """Generate via external provider (OpenAI/Claude) with system/user message split."""
        # Build system prompt from pre_condition + post_condition
        system_parts = []
        if pre_condition:
            system_parts.append(pre_condition)
        if post_condition:
            system_parts.append(f"Output format: {post_condition}")
        system_prompt = "\n\n".join(system_parts) if system_parts else None

        # Build user prompt with optional instructions
        user_prompt = prompt
        if user_instructions and user_instructions.strip():
            user_prompt = f"{prompt}\n\nAdditional instructions: {user_instructions}"

        if CHAT_DEBUG_LOGGING:
            logger.debug(
                f"{provider.title()} Chat Request",
                category=category,
                action=action,
                model=model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        else:
            logger.info(
                f"{provider.title()} chat request",
                category=category,
                action=action,
                model=model,
                prompt_length=len(prompt),
            )

        request = AIGenerationRequest(
            model=model,
            prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
        )
        response = adapter.generate(request)

        # Build normalized response dict (same keys as Ollama for frontend compatibility)
        response_data = {
            "response": response.content,
            "provider": response.provider,
            "model": response.model,
            "prompt_eval_count": response.prompt_tokens,
            "eval_count": response.completion_tokens,
        }

        if CHAT_DEBUG_LOGGING:
            logger.debug(
                f"{provider.title()} Chat Response",
                category=category,
                action=action,
                model=model,
                response_data=response_data,
            )
        else:
            logger.info(f"{provider.title()} chat completed", category=category, action=action, model=model)

        return response_data, 200

    def _log_usage(
        self,
        user_id: str,
        model: str,
        category: str | None,
        action: str | None,
        response_data: dict[str, Any],
        provider: str = "ollama",
    ) -> None:
        """Log AI usage for cost tracking. Fire-and-forget, never raises."""
        try:
            db = SessionLocal()
            try:
                self.usage_log_service.create_log(
                    db=db,
                    user_id=user_id,
                    endpoint="generate-unified",
                    model=model,
                    category=category,
                    action=action,
                    prompt_tokens=response_data.get("prompt_eval_count"),
                    eval_tokens=response_data.get("eval_count"),
                    total_duration_ns=response_data.get("total_duration"),
                )
            finally:
                db.close()
        except Exception as e:
            logger.warning("Failed to log usage", error=str(e), user_id=user_id, provider=provider)
