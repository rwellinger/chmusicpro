"""Claude Chat Routes - Provides endpoints for Claude model information."""

from flask import Blueprint, jsonify

from api.api_key_middleware import load_user_api_keys, require_api_key
from api.auth_middleware import jwt_required
from api.controllers.claude_chat_controller import ClaudeChatController
from utils.logger import logger


api_claude_chat_v1 = Blueprint("api_claude_chat_v1", __name__, url_prefix="/api/v1/claude/chat")

# Controller instance
claude_chat_controller = ClaudeChatController()


@api_claude_chat_v1.route("/models", methods=["GET"])
@jwt_required
def get_models():
    """Get list of available Claude Chat models."""
    try:
        load_user_api_keys()
        error = require_api_key("claude")
        if error:
            return jsonify(error[0]), error[1]

        models = claude_chat_controller.get_available_models()

        return jsonify({"models": models}), 200

    except Exception as e:
        logger.error("Error getting Claude models", error=str(e))
        return jsonify({"error": f"Failed to get models: {e}"}), 500
