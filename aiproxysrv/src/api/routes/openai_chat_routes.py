"""OpenAI Chat Routes - Provides endpoints for OpenAI model information."""

from flask import Blueprint, jsonify

from api.auth_middleware import jwt_required
from api.controllers.openai_chat_controller import OpenAIChatController
from utils.logger import logger


api_openai_chat_v1 = Blueprint("api_openai_chat_v1", __name__, url_prefix="/api/v1/openai/chat")

# Controller instance
openai_chat_controller = OpenAIChatController()


@api_openai_chat_v1.route("/models", methods=["GET"])
@jwt_required
def get_models():
    """Get list of available OpenAI Chat models."""
    try:
        models = openai_chat_controller.get_available_models()

        return jsonify({"models": models}), 200

    except Exception as e:
        logger.error("Error getting OpenAI models", error=str(e))
        return jsonify({"error": f"Failed to get models: {e}"}), 500
