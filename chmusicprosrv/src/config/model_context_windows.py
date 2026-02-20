"""
Model Context Window Configuration

Default values for AI model context window sizes (in tokens).
DB entries take precedence over these defaults via the orchestrator cache.
"""

DEFAULT_CONTEXT_WINDOWS = {
    # OpenAI Models (External) - GPT-5 Series
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
    # GPT-OSS Models (Ollama)
    "gpt-oss:20b": 8192,
    # DeepSeek Models
    "deepseek-r1:8b": 131072,
    # Apertus Models
    "MichelRosselli/apertus:latest": 65536,
    # LLaMA Models
    "llama2:7b": 4096,
    "llama2:13b": 4096,
    "llama2:70b": 4096,
    "llama3:8b": 8192,
    "llama3:70b": 8192,
    "llama3.1:8b": 131072,
    "llama3.1:70b": 131072,
    "llama3.2:1b": 131072,
    "llama3.2:3b": 131072,
    # Mistral Models
    "mistral:7b": 8192,
    "mistral:instruct": 8192,
    "mixtral:8x7b": 32768,
    # Gemma Models
    "gemma:2b": 8192,
    "gemma:7b": 8192,
    "gemma2:9b": 8192,
    "gemma2:27b": 8192,
    "gemma3:4b": 131072,
    # CodeLlama Models
    "codellama:7b": 16384,
    "codellama:13b": 16384,
    "codellama:34b": 16384,
    # Phi Models
    "phi3:mini": 4096,
    "phi3:medium": 4096,
    # Qwen Models
    "qwen:7b": 8192,
    "qwen:14b": 8192,
    "qwen2:7b": 32768,
    "qwen3:8b": 32768,
    "qwen3:30b": 32768,
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
        model_name: Model name (e.g., "gpt-4o", "gpt-oss:20b", "llama3.1:8b")

    Returns:
        Context window size in tokens

    Examples:
        >>> get_context_window_size("gpt-4o")
        128000
        >>> get_context_window_size("gpt-oss:20b")
        8192
        >>> get_context_window_size("llama3.1:8b")
        131072
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
