"""
Mock OpenAI Chat API - Simulates OpenAI Chat Completions for testing
"""

import time

from flask import Blueprint, jsonify, request


api_openai_chat_mock = Blueprint(
    "api_openai_chat_mock", __name__, url_prefix="/api/v1/openai/chat"
)


@api_openai_chat_mock.route("/models", methods=["GET"])
def get_models():
    """Mock GET /api/v1/openai/chat/models endpoint"""
    response = {
        "models": [
            # GPT-5 Series
            {"name": "gpt-5", "context_window": 200000},
            {"name": "gpt-5-mini", "context_window": 200000},
            {"name": "gpt-5-nano", "context_window": 200000},
            # GPT-4.1 Series
            {"name": "gpt-4.1", "context_window": 128000},
            {"name": "gpt-4.1-mini", "context_window": 128000},
            # GPT-4o Series
            {"name": "gpt-4o", "context_window": 128000},
            {"name": "gpt-4o-mini", "context_window": 128000},
        ]
    }
    return jsonify(response), 200


@api_openai_chat_mock.route("/completions", methods=["POST"])
def chat_completions():
    """
    Mock OpenAI Chat Completions endpoint
    Test scenarios:
    - "0001" in message → Success
    - "0002" in message → Auth Error (401)
    """
    raw_json = request.get_json(silent=True)

    if not raw_json:
        return jsonify({"error": "No JSON provided"}), 400

    # Extract messages from request
    messages = raw_json.get("messages", [])
    model = raw_json.get("model", "gpt-4o")

    if not messages:
        return jsonify({"error": "No messages provided"}), 400

    # Get last user message content for test scenarios
    last_message = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_message = msg.get("content", "")
            break

    # Test scenario: Auth error
    if "0002" in last_message:
        return jsonify(
            {
                "error": {
                    "message": "Invalid API key",
                    "type": "invalid_request_error",
                    "code": "invalid_api_key",
                }
            }
        ), 401

    # Mock successful response
    mock_response_text = f"This is a mock response from {model}. I received your message: '{last_message[:100]}...'. In a real scenario, I would provide a detailed response based on the OpenAI model's capabilities."

    response = {
        "id": f"chatcmpl-mock-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": mock_response_text},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": sum(len(m.get("content", "").split()) for m in messages),
            "completion_tokens": len(mock_response_text.split()),
            "total_tokens": sum(len(m.get("content", "").split()) for m in messages)
            + len(mock_response_text.split()),
        },
    }

    return jsonify(response), 200
