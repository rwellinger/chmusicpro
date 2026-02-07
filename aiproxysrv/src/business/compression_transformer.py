"""Compression Transformer - Pure functions for conversation compression logic."""

from typing import Any


def filter_compressible_messages(messages: list[Any], keep_recent: int) -> tuple[list[Any], list[Any], list[Any]]:
    """
    Separate messages into protected (system), old (to archive), and recent (to keep).

    Args:
        messages: List of message objects
        keep_recent: Number of recent user/assistant messages to keep

    Returns:
        Tuple of (protected_messages, old_messages, recent_messages)

    Examples:
        >>> messages = [
        ...     type('Message', (), {'role': 'system', 'content': 'System msg'}),
        ...     type('Message', (), {'role': 'user', 'content': 'Old user'}),
        ...     type('Message', (), {'role': 'assistant', 'content': 'Old assistant'}),
        ...     type('Message', (), {'role': 'user', 'content': 'Recent user'}),
        ... ]
        >>> protected, old, recent = filter_compressible_messages(messages, keep_recent=1)
        >>> len(protected)
        1
        >>> len(old)
        2
        >>> len(recent)
        1
    """
    # Separate protected (system) from compressible (user/assistant)
    protected_messages = [m for m in messages if m.role == "system"]
    compressible_messages = [m for m in messages if m.role in ["user", "assistant"]]

    # Check if compression is needed
    if len(compressible_messages) <= keep_recent:
        return protected_messages, [], compressible_messages

    # Split into old (to archive) and recent (to keep)
    old_messages = compressible_messages[:-keep_recent] if keep_recent > 0 else compressible_messages
    recent_messages = compressible_messages[-keep_recent:] if keep_recent > 0 else []

    return protected_messages, old_messages, recent_messages


def calculate_token_estimate(text: str, chars_per_token: int = 4) -> int:
    """
    Estimate token count from text length.

    Args:
        text: Text content
        chars_per_token: Average characters per token (default: 4 for OpenAI)

    Returns:
        Estimated token count

    Examples:
        >>> calculate_token_estimate("Hello world")
        2
        >>> calculate_token_estimate("Hello world", chars_per_token=3)
        3
        >>> calculate_token_estimate("")
        0
    """
    return int(len(text) / chars_per_token) if chars_per_token > 0 else 0


def build_summary_prompt(messages: list[Any], max_messages: int = 20) -> str:
    """
    Build prompt for AI summarization of messages.

    Args:
        messages: List of message objects with role and content
        max_messages: Maximum messages to include in prompt (default: 20)

    Returns:
        Formatted prompt string for summarization

    Examples:
        >>> messages = [
        ...     type('Message', (), {'role': 'user', 'content': 'Hello'}),
        ...     type('Message', (), {'role': 'assistant', 'content': 'Hi there!'}),
        ... ]
        >>> prompt = build_summary_prompt(messages, max_messages=2)
        >>> "Summarize this conversation" in prompt
        True
        >>> "user: Hello" in prompt
        True
    """
    # Include all messages, but with variable detail level
    conversation_text = "\n".join(
        [
            f"{msg.role}: {msg.content[: 500 if i < 5 else 150]}"  # First 5 messages: 500 chars, rest: 150 chars
            for i, msg in enumerate(messages[:max_messages])
        ]
    )

    return f"""Summarize this conversation in MAX 5 bullet points (max 50 words total):

{conversation_text}

Brief summary:"""


def format_summary_message(summary_content: str, archived_count: int) -> tuple[str, int]:
    """
    Format summary message with archive prefix and calculate prefix token count.

    Args:
        summary_content: AI-generated summary text
        archived_count: Number of messages archived

    Returns:
        Tuple of (formatted_message, prefix_token_count)

    Examples:
        >>> message, tokens = format_summary_message("Summary text", 10)
        >>> "[Summary: 10 msgs archived]" in message
        True
        >>> message.endswith("Summary text")
        True
        >>> tokens > 0
        True
    """
    # Keep prefix very short to minimize tokens
    prefix = f"[Summary: {archived_count} msgs archived]\n"

    # Rough token count for prefix (~ 1.3 tokens per word)
    prefix_token_count = int(len(prefix.split()) * 1.3)

    formatted_message = f"{prefix}{summary_content}"

    return formatted_message, prefix_token_count


def build_summary_messages(
    summary_prompt: str,
) -> list[dict[str, str]]:
    """
    Build message array for AI summarization call.

    Args:
        summary_prompt: Formatted summary prompt

    Returns:
        List of messages with system and user roles

    Examples:
        >>> messages = build_summary_messages("Summarize: user1: hi")
        >>> len(messages)
        2
        >>> messages[0]["role"]
        'system'
        >>> messages[1]["role"]
        'user'
    """
    return [
        {"role": "system", "content": "You are a helpful assistant that creates concise conversation summaries."},
        {"role": "user", "content": summary_prompt},
    ]


def calculate_actual_token_count_estimate(messages: list[dict[str, str]], chars_per_token: int = 4) -> int:
    """
    Calculate estimated token count for a list of messages.

    Args:
        messages: List of messages with role and content
        chars_per_token: Average characters per token (default: 4)

    Returns:
        Estimated total token count

    Examples:
        >>> messages = [
        ...     {"role": "user", "content": "Hello world"},
        ...     {"role": "assistant", "content": "Hi there!"}
        ... ]
        >>> tokens = calculate_actual_token_count_estimate(messages)
        >>> tokens > 0
        True
    """
    total_chars = sum(len(msg.get("content", "")) for msg in messages)
    return calculate_token_estimate(str(total_chars), chars_per_token)


def create_fallback_summary(messages: list[Any]) -> tuple[str, int]:
    """
    Create simple text-based fallback summary when AI summarization fails.

    Args:
        messages: List of message objects to summarize

    Returns:
        Tuple of (fallback_summary_text, estimated_token_count)

    Examples:
        >>> messages = [
        ...     type('Message', (), {'role': 'user', 'content': 'Test message content'}),
        ...     type('Message', (), {'role': 'assistant', 'content': 'Response content'}),
        ... ]
        >>> summary, tokens = create_fallback_summary(messages)
        >>> "Summary of 2 messages" in summary
        True
        >>> tokens > 0
        True
    """
    fallback_summary = f"Summary of {len(messages)} messages:\n" + "\n".join(
        [f"- {msg.role}: {msg.content[:100]}..." for msg in messages[:5]]
    )

    # Rough token estimate for fallback
    fallback_token_count = len(fallback_summary.split())

    return fallback_summary, fallback_token_count
