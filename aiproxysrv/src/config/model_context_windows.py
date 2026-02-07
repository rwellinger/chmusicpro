"""
Model Context Window Configuration

Maps AI model names to their context window sizes (in tokens).
Includes:
- OpenAI Models (gpt-4o, gpt-5, etc.)
- Ollama Models (llama3, gpt-oss, etc.)
"""

MODEL_CONTEXT_WINDOWS = {
    # OpenAI Models (External) - GPT-5 Series
    "gpt-5.1": 200000,  # GPT-5.1 (more efficient than gpt-5)
    "gpt-5.1-codex-mini": 200000,  # GPT-5.1 Codex Mini
    "gpt-5": 200000,  # GPT-5 base (estimated 200k)
    "gpt-5-pro": 200000,  # GPT-5 Pro
    "gpt-5-mini": 200000,  # GPT-5 Mini
    "gpt-5-nano": 200000,  # GPT-5 Nano
    "gpt-5-codex": 200000,  # GPT-5 Codex
    "gpt-5-chat-latest": 200000,  # GPT-5 Chat Latest
    # OpenAI Models - GPT-4.1 Series
    "gpt-4.1": 128000,  # GPT-4.1 base
    "gpt-4.1-mini": 128000,  # GPT-4.1 Mini
    "gpt-4.1-nano": 128000,  # GPT-4.1 Nano
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
    "deepseek-r1:8b": 131072,  # 128k context
    # Apertus Models
    "MichelRosselli/apertus:latest": 65536,  # 64k context
    # LLaMA Models
    "llama2:7b": 4096,
    "llama2:13b": 4096,
    "llama2:70b": 4096,
    "llama3:8b": 8192,
    "llama3:70b": 8192,
    "llama3.1:8b": 131072,  # 128k context
    "llama3.1:70b": 131072,  # 128k context
    "llama3.2:1b": 131072,  # 128k context
    "llama3.2:3b": 131072,  # 128k context
    # Mistral Models
    "mistral:7b": 8192,
    "mistral:instruct": 8192,
    "mixtral:8x7b": 32768,  # 32k context
    # Gemma Models
    "gemma:2b": 8192,
    "gemma:7b": 8192,
    "gemma2:9b": 8192,
    "gemma2:27b": 8192,
    "gemma3:4b": 131072,  # 128k context
    # CodeLlama Models
    "codellama:7b": 16384,  # 16k context
    "codellama:13b": 16384,
    "codellama:34b": 16384,
    # Phi Models
    "phi3:mini": 4096,
    "phi3:medium": 4096,
    # Qwen Models
    "qwen:7b": 8192,
    "qwen:14b": 8192,
    "qwen2:7b": 32768,  # 32k context
    # Default fallback
    "default": 2048,
}


def get_context_window_size(model_name: str) -> int:
    """
    Get context window size for a given model.

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
    # Try exact match first
    if model_name in MODEL_CONTEXT_WINDOWS:
        return MODEL_CONTEXT_WINDOWS[model_name]

    # Try base model match (e.g., "llama3:8b-instruct" -> "llama3:8b")
    base_model = model_name.split("-")[0]
    if base_model in MODEL_CONTEXT_WINDOWS:
        return MODEL_CONTEXT_WINDOWS[base_model]

    # Try family match (e.g., "llama3" from "llama3:custom")
    model_family = model_name.split(":")[0]
    for key in MODEL_CONTEXT_WINDOWS:
        if key.startswith(model_family):
            return MODEL_CONTEXT_WINDOWS[key]

    # Return default
    return MODEL_CONTEXT_WINDOWS["default"]


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

    Notes:
        - Claude: Delegates to claude_chat_transformer (all models = 200k)
        - OpenAI: Delegates to openai_chat_transformer (uses central config)
        - Future providers (deepseek, gemini): Fallback to central map

    Examples:
        >>> get_external_provider_context_window("claude", "claude-sonnet-4-5-20250929")
        200000
        >>> get_external_provider_context_window("openai", "gpt-4o")
        128000
        >>> get_external_provider_context_window("openai", "gpt-5.1")
        200000
    """
    if provider == "claude":
        # Delegate to Claude transformer (all Claude models = 200k)
        from business.claude_chat_transformer import (
            get_model_context_window as get_claude_context_window,
        )

        return get_claude_context_window(model_name)

    elif provider == "openai":
        # Delegate to OpenAI transformer (uses central config after refactor)
        from business.openai_chat_transformer import (
            get_model_context_window as get_openai_context_window,
        )

        return get_openai_context_window(model_name)

    else:
        # Future providers (deepseek, gemini, etc.) - fallback to central map
        return get_context_window_size(model_name)
