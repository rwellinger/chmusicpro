"""
OpenAI Cost API Routes - OpenAI Admin Cost Tracking
"""

from flask import Blueprint, jsonify

from api.auth_middleware import get_current_user_id, jwt_required
from api.controllers.openai_cost_controller import OpenAICostController


api_openai_costs_v1 = Blueprint("api_openai_costs_v1", __name__, url_prefix="/api/v1/openai/costs")

# Controller instances
cost_controller = OpenAICostController()


@api_openai_costs_v1.route("/current", methods=["GET"])
@jwt_required
def get_openai_current_month():
    """Get OpenAI costs for current month (cached with TTL)"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    response_data, status_code = cost_controller.get_current_month_costs()
    return jsonify(response_data), status_code


@api_openai_costs_v1.route("/all-time", methods=["GET"])
@jwt_required
def get_openai_all_time():
    """Get OpenAI all-time aggregated costs across all months"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    response_data, status_code = cost_controller.get_all_time_costs()
    return jsonify(response_data), status_code


@api_openai_costs_v1.route("/<int:year>/<int:month>", methods=["GET"])
@jwt_required
def get_openai_month(year: int, month: int):
    """Get OpenAI costs for specific month (cached forever for past months)"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Validate month
    if month < 1 or month > 12:
        return jsonify({"error": "Invalid month (must be 1-12)"}), 400

    response_data, status_code = cost_controller.get_month_costs(year, month)
    return jsonify(response_data), status_code
