"""API routes for model context window management (admin-only)"""

from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from sqlalchemy.orm import Session

from api.auth_middleware import domain_role_required, jwt_required
from api.controllers.model_context_window_controller import ModelContextWindowController
from db.database import get_db
from db.models import DomainType
from schemas.model_context_window_schemas import (
    ModelContextWindowCreate,
    ModelContextWindowUpdate,
)


api_model_context_v1 = Blueprint("api_model_context_v1", __name__, url_prefix="/api/v1/model-context-windows")


@api_model_context_v1.route("", methods=["GET"])
@jwt_required
@domain_role_required("admin", "owner", domain_type=DomainType.SYSTEM)
def list_entries():
    """
    Get all model context window entries

    Returns:
    - 200: List of model context window entries
    - 500: Server error
    """
    db: Session = next(get_db())
    try:
        result, status_code = ModelContextWindowController.list_entries(db)
        return jsonify(result), status_code
    finally:
        db.close()


@api_model_context_v1.route("", methods=["POST"])
@jwt_required
@domain_role_required("admin", "owner", domain_type=DomainType.SYSTEM)
def create_entry():
    """
    Create a new model context window entry

    Request Body: ModelContextWindowCreate schema

    Returns:
    - 201: Entry created successfully
    - 400: Validation error
    - 409: Model name already exists
    - 500: Server error
    """
    try:
        data = ModelContextWindowCreate.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = ModelContextWindowController.create_entry(db, data)
        return jsonify(result), status_code
    finally:
        db.close()


@api_model_context_v1.route("/<int:entry_id>", methods=["PUT"])
@jwt_required
@domain_role_required("admin", "owner", domain_type=DomainType.SYSTEM)
def update_entry(entry_id: int):
    """
    Update an existing model context window entry

    Request Body: ModelContextWindowUpdate schema

    Returns:
    - 200: Entry updated successfully
    - 400: Validation error
    - 404: Entry not found
    - 409: Model name already exists
    - 500: Server error
    """
    try:
        data = ModelContextWindowUpdate.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = ModelContextWindowController.update_entry(db, entry_id, data)
        return jsonify(result), status_code
    finally:
        db.close()


@api_model_context_v1.route("/<int:entry_id>", methods=["DELETE"])
@jwt_required
@domain_role_required("admin", "owner", domain_type=DomainType.SYSTEM)
def delete_entry(entry_id: int):
    """
    Delete a model context window entry

    Returns:
    - 200: Entry deleted successfully
    - 404: Entry not found
    - 500: Server error
    """
    db: Session = next(get_db())
    try:
        result, status_code = ModelContextWindowController.delete_entry(db, entry_id)
        return jsonify(result), status_code
    finally:
        db.close()
