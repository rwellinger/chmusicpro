"""API routes for lyric parsing rule management"""

from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from sqlalchemy.orm import Session

from api.auth_middleware import jwt_required
from api.controllers.lyric_parsing_rule_controller import LyricParsingRuleController
from db.database import get_db
from schemas.lyric_parsing_rule_schemas import (
    LyricParsingRuleCreate,
    LyricParsingRuleReorderRequest,
    LyricParsingRuleUpdate,
)


api_lyric_parsing_rule_v1 = Blueprint("api_lyric_parsing_rule_v1", __name__, url_prefix="/api/v1/lyric-parsing-rules")


@api_lyric_parsing_rule_v1.route("", methods=["GET"])
@jwt_required
def get_all_rules():
    """
    Get all lyric parsing rules

    Query Parameters:
    - rule_type (optional): Filter by rule type ('cleanup' or 'section')
    - active_only (optional): Only return active rules (true/false)

    Returns:
    - 200: List of lyric parsing rules
    - 500: Server error
    """
    rule_type = request.args.get("rule_type")
    active_only = request.args.get("active_only", "false").lower() == "true"

    db: Session = next(get_db())
    try:
        result, status_code = LyricParsingRuleController.get_all_rules(db, rule_type=rule_type, active_only=active_only)
        return jsonify(result), status_code
    finally:
        db.close()


@api_lyric_parsing_rule_v1.route("/<int:rule_id>", methods=["GET"])
@jwt_required
def get_rule_by_id(rule_id: int):
    """
    Get a specific lyric parsing rule by ID

    Returns:
    - 200: Rule details
    - 404: Rule not found
    - 500: Server error
    """
    db: Session = next(get_db())
    try:
        result, status_code = LyricParsingRuleController.get_rule_by_id(db, rule_id)
        return jsonify(result), status_code
    finally:
        db.close()


@api_lyric_parsing_rule_v1.route("", methods=["POST"])
@jwt_required
def create_rule():
    """
    Create a new lyric parsing rule

    Request Body: LyricParsingRuleCreate schema

    Returns:
    - 201: Rule created successfully
    - 400: Validation error
    - 409: Integrity error (duplicate)
    - 500: Server error
    """
    try:
        rule_data = LyricParsingRuleCreate.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = LyricParsingRuleController.create_rule(db, rule_data)
        return jsonify(result), status_code
    finally:
        db.close()


@api_lyric_parsing_rule_v1.route("/<int:rule_id>", methods=["PUT"])
@jwt_required
def update_rule(rule_id: int):
    """
    Update an existing lyric parsing rule

    Request Body: LyricParsingRuleUpdate schema

    Returns:
    - 200: Rule updated successfully
    - 400: Validation error
    - 404: Rule not found
    - 500: Server error
    """
    try:
        update_data = LyricParsingRuleUpdate.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = LyricParsingRuleController.update_rule(db, rule_id, update_data)
        return jsonify(result), status_code
    finally:
        db.close()


@api_lyric_parsing_rule_v1.route("/<int:rule_id>", methods=["DELETE"])
@jwt_required
def delete_rule(rule_id: int):
    """
    Delete a lyric parsing rule

    Returns:
    - 200: Rule deleted successfully
    - 404: Rule not found
    - 500: Server error
    """
    db: Session = next(get_db())
    try:
        result, status_code = LyricParsingRuleController.delete_rule(db, rule_id)
        return jsonify(result), status_code
    finally:
        db.close()


@api_lyric_parsing_rule_v1.route("/reorder", methods=["PATCH"])
@jwt_required
def reorder_rules():
    """
    Reorder lyric parsing rules

    Request Body: LyricParsingRuleReorderRequest schema
    Example: {"rule_ids": [3, 1, 2, 5, 4]}

    Returns:
    - 200: Rules reordered successfully
    - 400: Validation error
    - 404: One or more rules not found
    - 500: Server error
    """
    try:
        reorder_data = LyricParsingRuleReorderRequest.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = LyricParsingRuleController.reorder_rules(db, reorder_data)
        return jsonify(result), status_code
    finally:
        db.close()
