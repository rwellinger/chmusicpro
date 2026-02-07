"""
Mock Chat API - Simulates Ollama/Chat functionality for testing
"""

from flask import Blueprint, jsonify, request


api_chat_mock = Blueprint("api_chat_mock", __name__, url_prefix="/api/v1/ollama/chat")


@api_chat_mock.route("/generate-llama3-simple", methods=["POST"])
def generate_llama3_simple():
    """Mock llama3 simple generation"""
    raw_json = request.get_json(silent=True)

    if not raw_json:
        return jsonify({"error": "No JSON provided"}), 400

    prompt = raw_json.get("prompt", "")

    # Test scenarios based on prompt content
    if "0002" in prompt:
        return jsonify({"error": "Mock API: Token invalid"}), 401

    # Mock successful response
    response = {
        "model": "llama3.2:3b",
        "created_at": "2025-09-22T10:00:00.000Z",
        "response": f"Improved prompt: {prompt} - mock enhanced version",
        "done": True,
        "done_reason": "stop",
        "total_duration": 1500000000,
        "load_duration": 100000000,
        "prompt_eval_count": 10,
        "prompt_eval_duration": 200000000,
        "eval_count": 15,
        "eval_duration": 300000000,
    }

    return jsonify(response), 200


@api_chat_mock.route("/generate-gpt-oss-simple", methods=["POST"])
def generate_gpt_oss_simple():
    """Mock gpt-oss simple generation"""
    raw_json = request.get_json(silent=True)

    if not raw_json:
        return jsonify({"error": "No JSON provided"}), 400

    prompt = raw_json.get("prompt", "")

    # Test scenarios based on prompt content
    if "0002" in prompt:
        return jsonify({"error": "Mock API: Token invalid"}), 401

    # Mock successful response
    response = {
        "model": "gpt-oss:20b",
        "created_at": "2025-09-22T10:00:00.000Z",
        "response": f"Translated lyrics: {prompt} - mock translation",
        "done": True,
        "done_reason": "stop",
        "total_duration": 2500000000,
        "load_duration": 150000000,
        "prompt_eval_count": 20,
        "prompt_eval_duration": 400000000,
        "eval_count": 30,
        "eval_duration": 600000000,
    }

    return jsonify(response), 200


@api_chat_mock.route("/generate-lyrics", methods=["POST"])
def generate_lyrics():
    """Mock lyrics generation"""
    raw_json = request.get_json(silent=True)

    if not raw_json:
        return jsonify({"error": "No JSON provided"}), 400

    input_text = raw_json.get("input_text", "")

    # Test scenarios based on input text
    if "0002" in input_text:
        return jsonify({"error": "Mock API: Token invalid"}), 401

    if "0003" in input_text:
        return jsonify({"error": "Mock API: Lyric generation failed"}), 500

    # Mock successful lyric generation
    mock_lyrics = f"""[Verse 1]
{input_text[:50]}...
Dreams and hopes collide
In this rhythm we find

[Chorus]
Sing it loud, sing it true
Every word speaks of you
In this melody we create
Love and music never wait

[Verse 2]
Through the verses we explore
Stories told and so much more
Harmony in every line
Your thoughts and mine combine

[Chorus]
Sing it loud, sing it true
Every word speaks of you
In this melody we create
Love and music never wait"""

    response = {
        "model": "gpt-oss:20b",
        "created_at": "2025-09-22T10:00:00.000Z",
        "response": mock_lyrics,
        "done": True,
        "done_reason": "stop",
        "total_duration": 3000000000,
        "load_duration": 200000000,
        "prompt_eval_count": 25,
        "prompt_eval_duration": 500000000,
        "eval_count": 80,
        "eval_duration": 1200000000,
    }

    return jsonify(response), 200
