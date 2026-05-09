"""Unified AI Adapter - Provider-agnostic interface for AI text generation.

Wraps OpenAI and Claude API clients behind a common interface.
Used by ChatOrchestrator to route requests to the configured provider.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from config.ai_config import (
    PROVIDER_CLAUDE,
    PROVIDER_OPENAI,
    AIConfig,
)
from utils.logger import logger


@dataclass
class AIGenerationRequest:
    """Provider-agnostic generation request."""

    model: str
    prompt: str
    temperature: float = 0.7
    max_tokens: int | None = None
    system_prompt: str | None = None


@dataclass
class AIGenerationResponse:
    """Provider-agnostic generation response."""

    content: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    raw_response: dict[str, Any] = field(default_factory=dict)


class AIAdapter(ABC):
    """Abstract base class for AI provider adapters."""

    @abstractmethod
    def generate(self, request: AIGenerationRequest) -> AIGenerationResponse:
        """Generate text from the AI provider."""

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return provider identifier."""


class OpenAIAdapter(AIAdapter):
    """Adapter for OpenAI Chat API. Uses existing transformer functions."""

    def __init__(self):
        from adapters.openai.api_client import OpenAIAPIClient

        self.client = OpenAIAPIClient()

    def generate(self, request: AIGenerationRequest) -> AIGenerationResponse:
        """Generate via OpenAI Chat Completions API."""
        from business.openai_chat_transformer import build_chat_payload, parse_chat_response

        # Build messages array from system_prompt + user prompt
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        payload = build_chat_payload(
            model=request.model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        response_json = self.client.chat_completion(payload)
        content, prompt_tokens, completion_tokens = parse_chat_response(response_json)

        return AIGenerationResponse(
            content=content,
            provider=PROVIDER_OPENAI,
            model=request.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            raw_response=response_json,
        )

    def get_provider_name(self) -> str:
        return PROVIDER_OPENAI


class ClaudeAdapter(AIAdapter):
    """Adapter for Claude Messages API. Uses existing transformer functions."""

    def __init__(self):
        from adapters.claude.api_client import ClaudeAPIClient

        self.client = ClaudeAPIClient()

    def generate(self, request: AIGenerationRequest) -> AIGenerationResponse:
        """Generate via Claude Messages API."""
        from business.claude_chat_transformer import build_messages_payload, parse_messages_response
        from config.settings import CLAUDE_MAX_TOKENS

        # Build messages - Claude handles system separately via build_messages_payload
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        # Claude requires max_tokens - use configured fallback
        max_tokens = request.max_tokens if request.max_tokens and request.max_tokens > 0 else CLAUDE_MAX_TOKENS

        payload = build_messages_payload(
            model=request.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=request.temperature,
        )

        response_json = self.client.messages_create(payload)
        content, input_tokens, output_tokens = parse_messages_response(response_json)

        return AIGenerationResponse(
            content=content,
            provider=PROVIDER_CLAUDE,
            model=request.model,
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
            raw_response=response_json,
        )

    def get_provider_name(self) -> str:
        return PROVIDER_CLAUDE


class AIAdapterFactory:
    """Factory to create the appropriate AI adapter based on provider name."""

    _adapters = {
        PROVIDER_OPENAI: OpenAIAdapter,
        PROVIDER_CLAUDE: ClaudeAdapter,
    }

    @staticmethod
    def create_adapter(provider: str) -> AIAdapter:
        """Create adapter for the given provider. Validates provider is available."""
        if not AIConfig.validate_provider(provider):
            available = AIConfig.get_available_providers()
            raise ValueError(f"Provider '{provider}' is not available. Available providers: {available}")

        adapter_class = AIAdapterFactory._adapters.get(provider)
        if not adapter_class:
            raise ValueError(f"Unknown provider: {provider}")

        logger.debug("Creating AI adapter", provider=provider)
        return adapter_class()
