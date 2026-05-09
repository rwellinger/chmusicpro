"""
Model Context Window Configuration

Default values for AI model context window sizes (in tokens).
DB entries take precedence over these defaults via the orchestrator cache.
"""

DEFAULT_CONTEXT_WINDOWS = {
    # OpenAI Models - GPT-5 Series
    "gpt-5.1": 200000,
    "gpt-5.1-codex-mini": 200000,
    "gpt-5": 200000,
    "gpt-5-pro": 200000,
    "gpt-5-mini": 200000,
    "gpt-5-nano": 200000,
    "gpt-5-codex": 200000,
    "gpt-5-chat-latest": 200000,
    # OpenAI Models - GPT-4.1 Series
    "gpt-4.1": 128000,
    "gpt-4.1-mini": 128000,
    "gpt-4.1-nano": 128000,
    # OpenAI Models - GPT-4o Series
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    # OpenAI Models - GPT-4 Series
    "gpt-4-turbo": 128000,
    "gpt-4": 8192,
    # OpenAI Models - GPT-3.5 Series
    "gpt-3.5-turbo": 16385,
    "gpt-3.5-turbo-16k": 16385,
    # Default fallback
    "default": 2048,
}

# Backward compatibility alias
MODEL_CONTEXT_WINDOWS = DEFAULT_CONTEXT_WINDOWS


def get_context_window_size(model_name: str) -> int:
    """
    Get context window size for a given model (cached DB lookup).

    Delegates to the orchestrator which uses an in-memory cache
    backed by the model_context_windows DB table.
    Falls back to DEFAULT_CONTEXT_WINDOWS if DB is unavailable.

    Args:
        model_name: Model name (e.g., "gpt-4o", "gpt-4.1-mini")

    Returns:
        Context window size in tokens

    Examples:
        >>> get_context_window_size("gpt-4o")
        128000
        >>> get_context_window_size("unknown-model")
        2048
    """
    from business.model_context_window_orchestrator import model_context_window_orchestrator

    return model_context_window_orchestrator.get_context_window(model_name)


def get_external_provider_context_window(provider: str, model_name: str) -> int:
    """
    Get context window for external providers (OpenAI, Claude, etc.).

    Delegates to provider-specific transformers to avoid hardcoding
    provider models in central config.

    Args:
        provider: External provider name ('openai', 'claude', etc.)
        model_name: Model name

    Returns:
        Context window size in tokens

    Examples:
        >>> get_external_provider_context_window("claude", "claude-sonnet-4-5-20250929")
        200000
        >>> get_external_provider_context_window("openai", "gpt-4o")
        128000
    """
    if provider == "claude":
        from business.claude_chat_transformer import (
            get_model_context_window as get_claude_context_window,
        )

        return get_claude_context_window(model_name)

    elif provider == "openai":
        from business.openai_chat_transformer import (
            get_model_context_window as get_openai_context_window,
        )

        return get_openai_context_window(model_name)

    else:
        return get_context_window_size(model_name)
