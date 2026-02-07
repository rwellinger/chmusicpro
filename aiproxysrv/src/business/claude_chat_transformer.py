"""Claude Chat Transformer - Pure functions for Claude Messages API payload building and response parsing."""

from typing import Any


def build_messages_payload(
    model: str, messages: list[dict[str, str]], max_tokens: int, temperature: float = 0.7
) -> dict[str, Any]:
    """
    Build payload for Claude Messages API request.

    Args:
        model: Claude model name (e.g., "claude-sonnet-4-5-20250929")
        messages: List of messages with role and content (user/assistant only)
        max_tokens: Maximum tokens to generate (REQUIRED by Claude API)
        temperature: Sampling temperature (0.0-1.0)

    Returns:
        Dictionary with Claude Messages API payload

    Notes:
        - System messages must be extracted and placed in separate 'system' field
        - Claude API requires max_tokens (not optional like OpenAI)
        - Temperature range is 0.0-1.0 (not 0.0-2.0 like OpenAI)

    Examples:
        >>> payload = build_messages_payload(
        ...     "claude-sonnet-4-5-20250929",
        ...     [{"role": "user", "content": "Hi"}],
        ...     max_tokens=1024
        ... )
        >>> payload["model"]
        'claude-sonnet-4-5-20250929'
        >>> payload["max_tokens"]
        1024
    """
    # Extract system message if present (Claude expects it in separate field)
    system_message = None
    filtered_messages = []

    for msg in messages:
        if msg.get("role") == "system":
            system_message = msg.get("content", "")
        else:
            filtered_messages.append(msg)

    # Build base payload
    payload: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,  # Required by Claude API
        "messages": filtered_messages,
    }

    # Add system message if present
    if system_message:
        payload["system"] = system_message

    # Add temperature (0.0-1.0 range)
    if temperature is not None:
        payload["temperature"] = max(0.0, min(1.0, temperature))  # Clamp to 0.0-1.0

    return payload


def parse_messages_response(response_json: dict[str, Any]) -> tuple[str, int, int]:
    """
    Parse Claude Messages API response and extract content + token counts.

    Args:
        response_json: Claude Messages API response JSON

    Returns:
        Tuple of (assistant_content, input_tokens, output_tokens)

    Raises:
        ValueError: If response format is invalid

    Notes:
        - Claude returns content as array of objects: [{"type": "text", "text": "..."}]
        - Usage has "input_tokens" and "output_tokens" (not prompt_tokens/completion_tokens)

    Examples:
        >>> response = {
        ...     "content": [{"type": "text", "text": "Hello!"}],
        ...     "usage": {"input_tokens": 10, "output_tokens": 5}
        ... }
        >>> content, input_tokens, output_tokens = parse_messages_response(response)
        >>> content
        'Hello!'
        >>> input_tokens
        10
        >>> output_tokens
        5
    """
    if "content" not in response_json or len(response_json["content"]) == 0:
        raise ValueError("Invalid API response format: no content found")

    # Extract text from content array
    content_blocks = response_json["content"]
    text_parts = []
    for block in content_blocks:
        if block.get("type") == "text":
            text_parts.append(block.get("text", ""))

    content = "".join(text_parts)

    # Extract token usage
    usage = response_json.get("usage", {})
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    return content, input_tokens, output_tokens


def get_model_context_window(_model_name: str) -> int:
    """
    Get context window size for Claude model.

    Args:
        _model_name: Claude model name (unused, all models have same context window)

    Returns:
        Context window size in tokens

    Notes:
        - All current Claude models have 200k context window
        - This includes Sonnet, Haiku, and Opus variants

    Examples:
        >>> get_model_context_window("claude-sonnet-4-5-20250929")
        200000
        >>> get_model_context_window("claude-haiku-4-5-20250929")
        200000
        >>> get_model_context_window("claude-opus-4-5-20251101")
        200000
    """
    # All current Claude models have 200k context window
    return 200000


def get_available_models(models_config: str) -> list[dict[str, Any]]:
    """
    Parse comma-separated model names and return list with context windows.

    Args:
        models_config: Comma-separated model names (e.g., "claude-sonnet-4-5-20250929,claude-haiku-4-5-20250929")

    Returns:
        List of model dictionaries with name and context_window

    Examples:
        >>> models = get_available_models("claude-sonnet-4-5-20250929,claude-haiku-4-5-20250929")
        >>> len(models)
        2
        >>> models[0]["name"]
        'claude-sonnet-4-5-20250929'
        >>> models[0]["context_window"]
        200000
    """
    model_names = [m.strip() for m in models_config.split(",") if m.strip()]

    models = []
    for model_name in model_names:
        models.append(
            {
                "name": model_name,
                "context_window": get_model_context_window(model_name),
            }
        )

    return models


def get_model_context_window_from_id(model_id: str) -> int:
    """
    Map Claude model ID to context window size.

    Since Anthropic API doesn't return context_window in /models response,
    we maintain a mapping based on model ID patterns.

    Args:
        model_id: Claude model ID (e.g., "claude-sonnet-4-5-20250929")

    Returns:
        Context window size in tokens

    Notes:
        - All current Claude 3+ models have 200k context window
        - Haiku, Sonnet, Opus 4.x/5.x series: 200k
        - Legacy models (Claude 2.x): 100k
        - Unknown models: Default to 200k (safe for new models)

    Examples:
        >>> get_model_context_window_from_id("claude-sonnet-4-5-20250929")
        200000
        >>> get_model_context_window_from_id("claude-haiku-4-5-20250929")
        200000
        >>> get_model_context_window_from_id("claude-opus-4-5-20251101")
        200000
        >>> get_model_context_window_from_id("claude-2.1")
        100000
        >>> get_model_context_window_from_id("claude-unknown-new-model")
        200000
    """
    # Legacy Claude 2.x models (100k context)
    if "claude-2" in model_id.lower() or "claude-instant" in model_id.lower():
        return 100000

    # All modern Claude 3+ models (Haiku, Sonnet, Opus 4.x/5.x series)
    # Default to 200k for future models (safe assumption for new releases)
    return 200000


def parse_configured_claude_models(models_config: str) -> list[str]:
    """
    Parse comma-separated Claude model names from configuration.

    Pure function - no side effects, fully unit-testable

    Args:
        models_config: Comma-separated model names (e.g., "claude-sonnet-4-5-20250929, claude-haiku-4-5-20250929")
                       Empty string returns empty list (= no whitelist, show all models)

    Returns:
        List of trimmed model names (duplicates removed, order preserved)

    Examples:
        >>> parse_configured_claude_models("claude-sonnet-4-5-20250929, claude-haiku-4-5-20250929")
        ['claude-sonnet-4-5-20250929', 'claude-haiku-4-5-20250929']
        >>> parse_configured_claude_models("  model1,  ,model2  ")
        ['model1', 'model2']
        >>> parse_configured_claude_models("")
        []
    """
    if not models_config or not models_config.strip():
        return []

    # Split, strip, filter empty, preserve order, remove duplicates
    models = []
    seen = set()
    for model in models_config.split(","):
        model_stripped = model.strip()
        if model_stripped and model_stripped not in seen:
            models.append(model_stripped)
            seen.add(model_stripped)

    return models


def transform_api_model_to_frontend(api_model: dict[str, Any]) -> dict[str, Any] | None:
    """
    Transform Anthropic API model to frontend format.

    Pure function - no side effects, fully unit-testable

    Args:
        api_model: Raw model from Anthropic API {
            "id": "claude-sonnet-4-5-20250929",
            "created_at": "2025-01-15T12:00:00Z",
            "display_name": "Claude Sonnet 4.5",
            "type": "model"
        }

    Returns:
        Frontend model dict {"name": str, "context_window": int}
        None if api_model has no valid "id"

    Notes:
        - Anthropic API uses "id" field (not "name")
        - API doesn't provide context_window → map manually
        - Filter out non-model types (embeddings, etc.)

    Examples:
        >>> api_model = {"id": "claude-sonnet-4-5-20250929", "type": "model"}
        >>> transform_api_model_to_frontend(api_model)
        {'name': 'claude-sonnet-4-5-20250929', 'context_window': 200000}
        >>> api_model = {"id": "", "type": "model"}
        >>> transform_api_model_to_frontend(api_model)
        None
        >>> api_model = {"id": "claude-embedding-v1", "type": "embedding"}
        >>> transform_api_model_to_frontend(api_model)
        None
    """
    model_id = api_model.get("id", "")
    model_type = api_model.get("type", "")

    # Validate model ID
    if not model_id or not model_id.strip():
        return None

    # Filter out non-chat models (embeddings, fine-tuned models, etc.)
    # Only include type="model" (chat models)
    if model_type != "model":
        return None

    return {
        "name": model_id,
        "context_window": get_model_context_window_from_id(model_id),
    }


def transform_api_models_to_frontend(api_models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Transform list of Anthropic API models to frontend format.

    Pure function - no side effects, fully unit-testable

    Args:
        api_models: List of raw models from Anthropic API response["data"]

    Returns:
        List of frontend model dicts (skips models without valid IDs or wrong type)

    Examples:
        >>> api_models = [
        ...     {"id": "claude-sonnet-4-5-20250929", "type": "model"},
        ...     {"id": "", "type": "model"},  # Skipped (no ID)
        ...     {"id": "claude-haiku-4-5-20250929", "type": "model"},
        ...     {"id": "claude-embedding-v1", "type": "embedding"}  # Skipped (not chat model)
        ... ]
        >>> result = transform_api_models_to_frontend(api_models)
        >>> len(result)
        2
        >>> result[0]["name"]
        'claude-sonnet-4-5-20250929'
        >>> result[0]["context_window"]
        200000
    """
    frontend_models = []

    for api_model in api_models:
        frontend_model = transform_api_model_to_frontend(api_model)
        if frontend_model:
            frontend_models.append(frontend_model)

    return frontend_models


def filter_models_by_whitelist(models: list[dict[str, Any]], whitelist: list[str]) -> list[dict[str, Any]]:
    """
    Filter model list by whitelist configuration.

    Pure function - no side effects, fully unit-testable

    Args:
        models: List of frontend model dicts [{"name": str, "context_window": int}, ...]
        whitelist: List of allowed model names (empty = no filtering)

    Returns:
        Filtered list of models (only models in whitelist)
        If whitelist is empty, returns all models unchanged

    Examples:
        >>> models = [
        ...     {"name": "claude-sonnet-4-5-20250929", "context_window": 200000},
        ...     {"name": "claude-haiku-4-5-20250929", "context_window": 200000},
        ...     {"name": "claude-opus-4-5-20251101", "context_window": 200000},
        ... ]
        >>> whitelist = ["claude-sonnet-4-5-20250929", "claude-haiku-4-5-20250929"]
        >>> result = filter_models_by_whitelist(models, whitelist)
        >>> len(result)
        2
        >>> result[0]["name"]
        'claude-sonnet-4-5-20250929'
        >>> # Empty whitelist = no filtering
        >>> result = filter_models_by_whitelist(models, [])
        >>> len(result)
        3
    """
    # Empty whitelist = show all models
    if not whitelist:
        return models

    # Convert whitelist to set for O(1) lookup
    whitelist_set = set(whitelist)

    # Filter models
    filtered_models = []
    for model in models:
        if model.get("name") in whitelist_set:
            filtered_models.append(model)

    return filtered_models
