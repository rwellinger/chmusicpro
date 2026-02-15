"""AI Configuration Routes - Expose AI provider configuration to frontend."""

from flask import Blueprint, jsonify

from api.auth_middleware import jwt_required
from api.controllers.ai_config_controller import AIConfigController


api_ai_config_v1 = Blueprint("api_ai_config_v1", __name__, url_prefix="/api/v1/ai-config")

ai_config_controller = AIConfigController()


@api_ai_config_v1.route("/", methods=["GET"])
@jwt_required
def get_ai_config():
    """Get current AI configuration (mode, providers, etc.)"""
    config = ai_config_controller.get_config()
    return jsonify(config), 200
