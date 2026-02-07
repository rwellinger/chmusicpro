"""OpenAI Chat Transformer - Pure functions for OpenAI API payload building and response parsing."""

from typing import Any


def build_chat_payload(
    model: str, messages: list[dict[str, str]], temperature: float = 0.7, max_tokens: int | None = None
) -> dict[str, Any]:
    """
    Build payload for OpenAI Chat API request.

    Args:
        model: OpenAI model name (e.g., "gpt-4o")
        messages: List of messages with role and content
        temperature: Sampling temperature (0.0-2.0)
        max_tokens: Maximum tokens to generate (optional)

    Returns:
        Dictionary with OpenAI API payload

    Examples:
        >>> payload = build_chat_payload("gpt-4o", [{"role": "user", "content": "Hi"}])
        >>> payload["model"]
        'gpt-4o'
        >>> payload["temperature"]
        0.7

        >>> payload = build_chat_payload("gpt-5", [{"role": "user", "content": "Hi"}], temperature=0.5)
        >>> "temperature" in payload
        False
    """
    payload = {
        "model": model,
        "messages": messages,
    }

    # GPT-5 models don't support custom temperature (only default 1.0)
    # Other models support temperature 0.0-2.0
    if not model.startswith("gpt-5"):
        payload["temperature"] = temperature

    if max_tokens:
        # max_completion_tokens is the new standard (max_tokens is deprecated)
        payload["max_completion_tokens"] = max_tokens

    return payload


def parse_chat_response(response_json: dict[str, Any]) -> tuple[str, int, int]:
    """
    Parse OpenAI Chat API response and extract content + token counts.

    Args:
        response_json: OpenAI API response JSON

    Returns:
        Tuple of (assistant_content, prompt_tokens, completion_tokens)

    Raises:
        ValueError: If response format is invalid

    Examples:
        >>> response = {
        ...     "choices": [{"message": {"content": "Hello!"}}],
        ...     "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        ... }
        >>> content, prompt, completion = parse_chat_response(response)
        >>> content
        'Hello!'
        >>> prompt
        10
        >>> completion
        5
    """
    if "choices" not in response_json or len(response_json["choices"]) == 0:
        raise ValueError("Invalid API response format: no choices found")

    choice = response_json["choices"][0]
    content = choice.get("message", {}).get("content", "")

    # Extract token usage
    usage = response_json.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)

    return content, prompt_tokens, completion_tokens


def get_model_context_window(model_name: str) -> int:
    """
    Get context window size for OpenAI model.

    Args:
        model_name: OpenAI model name

    Returns:
        Context window size in tokens

    Notes:
        - First tries exact match in central config
        - Then uses pattern-based fallback for new models (gpt-5.2, gpt-5.3, etc.)
        - New models in same family automatically get correct context window

    Examples:
        >>> get_model_context_window("gpt-5")
        200000
        >>> get_model_context_window("gpt-5.2")
        200000
        >>> get_model_context_window("gpt-4o")
        128000
        >>> get_model_context_window("gpt-3.5-turbo")
        16385
        >>> get_model_context_window("unknown-model")
        2048
    """
    from config.model_context_windows import MODEL_CONTEXT_WINDOWS

    # Try exact match first
    if model_name in MODEL_CONTEXT_WINDOWS:
        return MODEL_CONTEXT_WINDOWS[model_name]

    # Pattern-based fallback for new models (like Claude transformer does)
    # GPT-5 series (gpt-5, gpt-5.1, gpt-5.2, gpt-5-mini, etc.) → 200k
    if model_name.startswith("gpt-5"):
        return 200000

    # GPT-4o series (gpt-4o, gpt-4o-mini, etc.) → 128k
    if model_name.startswith("gpt-4o"):
        return 128000

    # GPT-4.1 series (gpt-4.1, gpt-4.1-mini, etc.) → 128k
    if model_name.startswith("gpt-4.1"):
        return 128000

    # GPT-4 series (gpt-4, gpt-4-turbo, etc.) → 8k
    if model_name.startswith("gpt-4"):
        return 8192

    # GPT-3.5 series → 16k
    if model_name.startswith("gpt-3.5"):
        return 16385

    # Unknown models → default
    return MODEL_CONTEXT_WINDOWS.get("default", 2048)


def get_available_models(models_config: str) -> list[dict[str, Any]]:
    """
    Parse comma-separated model names and return list with context windows.

    Args:
        models_config: Comma-separated model names (e.g., "gpt-4o,gpt-3.5-turbo")

    Returns:
        List of model dictionaries with name and context_window

    Examples:
        >>> models = get_available_models("gpt-4o,gpt-3.5-turbo")
        >>> len(models)
        2
        >>> models[0]["name"]
        'gpt-4o'
        >>> models[0]["context_window"]
        128000
        >>> models[1]["context_window"]
        16385
    """
    model_names = [m.strip() for m in models_config.split(",")]

    models = []
    for model_name in model_names:
        models.append(
            {
                "name": model_name,
                "context_window": get_model_context_window(model_name),
            }
        )

    return models
