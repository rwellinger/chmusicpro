"""API routes for workshop management"""

from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from sqlalchemy.orm import Session

from api.auth_middleware import jwt_required
from api.controllers.workshop_controller import WorkshopController
from db.database import get_db
from schemas.workshop_schemas import WorkshopCreateRequest, WorkshopUpdateRequest


api_workshop_v1 = Blueprint("api_workshop_v1", __name__, url_prefix="/api/v1/workshops")


@api_workshop_v1.route("", methods=["POST"])
@jwt_required
def create_workshop():
    """Create a new workshop"""
    try:
        workshop_data = WorkshopCreateRequest.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = WorkshopController.create_workshop(db, workshop_data)
        return jsonify(result), status_code
    finally:
        db.close()


@api_workshop_v1.route("", methods=["GET"])
@jwt_required
def list_workshops():
    """Get list of workshops with pagination, search and filtering"""
    try:
        limit = int(request.args.get("limit", 20))
        offset = int(request.args.get("offset", 0))

        if limit <= 0 or limit > 100:
            return jsonify({"error": "Limit must be between 1 and 100"}), 400
        if offset < 0:
            return jsonify({"error": "Offset must be >= 0"}), 400

    except ValueError:
        return jsonify({"error": "Invalid limit or offset parameter"}), 400

    search = request.args.get("search", "").strip()
    phase = request.args.get("phase", None)
    sort_by = request.args.get("sort_by", "created_at")
    sort_direction = request.args.get("sort_direction", "desc")

    valid_sort_fields = ["created_at", "updated_at", "title"]
    if sort_by not in valid_sort_fields:
        return jsonify({"error": f"Invalid sort_by field. Must be one of: {valid_sort_fields}"}), 400

    if sort_direction not in ["asc", "desc"]:
        return jsonify({"error": "Invalid sort_direction. Must be 'asc' or 'desc'"}), 400

    if phase and phase not in ["connect", "collect", "shape", "completed"]:
        return jsonify({"error": "Invalid phase. Must be one of: connect, collect, shape, completed"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = WorkshopController.get_workshops(
            db=db,
            limit=limit,
            offset=offset,
            search=search,
            phase=phase,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )
        return jsonify(result), status_code
    finally:
        db.close()


@api_workshop_v1.route("/<workshop_id>", methods=["GET"])
@jwt_required
def get_workshop(workshop_id: str):
    """Get a specific workshop by ID"""
    db: Session = next(get_db())
    try:
        result, status_code = WorkshopController.get_workshop_by_id(db, workshop_id)
        return jsonify(result), status_code
    finally:
        db.close()


@api_workshop_v1.route("/<workshop_id>", methods=["PUT"])
@jwt_required
def update_workshop(workshop_id: str):
    """Update an existing workshop"""
    try:
        update_data = WorkshopUpdateRequest.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = WorkshopController.update_workshop(db, workshop_id, update_data)
        return jsonify(result), status_code
    finally:
        db.close()


@api_workshop_v1.route("/<workshop_id>", methods=["DELETE"])
@jwt_required
def delete_workshop(workshop_id: str):
    """Delete a workshop"""
    db: Session = next(get_db())
    try:
        result, status_code = WorkshopController.delete_workshop(db, workshop_id)
        return jsonify(result), status_code
    finally:
        db.close()


@api_workshop_v1.route("/<workshop_id>/export-to-sketch", methods=["POST"])
@jwt_required
def export_to_sketch(workshop_id: str):
    """Export workshop content to a new SongSketch"""
    db: Session = next(get_db())
    try:
        result, status_code = WorkshopController.export_to_sketch(db, workshop_id)
        return jsonify(result), status_code
    finally:
        db.close()
