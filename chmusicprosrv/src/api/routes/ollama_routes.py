"""Ollama Routes - Proxy routes for Ollama API."""

from flask import Blueprint, jsonify

from api.auth_middleware import jwt_required
from api.controllers.ollama_controller import OllamaController
from utils.logger import logger


api_ollama_v1 = Blueprint("api_ollama_v1", __name__, url_prefix="/api/v1/ollama")

# Controller instance
ollama_controller = OllamaController()


@api_ollama_v1.route("/tags", methods=["GET"])
@jwt_required
def get_models():
    """Get available Ollama models."""
    try:
        response_data, status_code = ollama_controller.get_models()
        return jsonify(response_data), status_code

    except Exception as e:
        logger.error("Error in get_models route", error=str(e))
        return jsonify({"error": f"Failed to get models: {e}"}), 500


@api_ollama_v1.route("/chat/models", methods=["GET"])
@jwt_required
def get_chat_models():
    """Get available Ollama chat models based on configuration."""
    try:
        response_data, status_code = ollama_controller.get_available_chat_models()
        return jsonify(response_data), status_code

    except Exception as e:
        logger.error("Error in get_chat_models route", error=str(e))
        return jsonify({"error": f"Failed to get chat models: {e}"}), 500
