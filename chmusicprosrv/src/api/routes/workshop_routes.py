"""API routes for workshop management"""

from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from sqlalchemy.orm import Session

from api.auth_middleware import get_current_domain_id, get_current_user_id, jwt_required
from api.controllers.workshop_controller import WorkshopController
from db.database import get_db
from schemas.project_asset_schemas import AssignToProjectRequest
from schemas.workshop_schemas import WorkshopCreateRequest, WorkshopUpdateRequest


api_workshop_v1 = Blueprint("api_workshop_v1", __name__, url_prefix="/api/v1/workshops")


@api_workshop_v1.route("", methods=["POST"])
@jwt_required
def create_workshop():
    """Create a new workshop"""
    user_id = get_current_user_id()
    domain_id = get_current_domain_id()
    if not user_id or not domain_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        workshop_data = WorkshopCreateRequest.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = WorkshopController.create_workshop(db, str(user_id), str(domain_id), workshop_data)
        return jsonify(result), status_code
    finally:
        db.close()


@api_workshop_v1.route("", methods=["GET"])
@jwt_required
def list_workshops():
    """Get list of workshops with pagination, search and filtering"""
    domain_id = get_current_domain_id()
    if not domain_id:
        return jsonify({"error": "Unauthorized"}), 401

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
            domain_id=str(domain_id),
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
    domain_id = get_current_domain_id()
    if not domain_id:
        return jsonify({"error": "Unauthorized"}), 401

    db: Session = next(get_db())
    try:
        result, status_code = WorkshopController.get_workshop_by_id(db, str(domain_id), workshop_id)
        return jsonify(result), status_code
    finally:
        db.close()


@api_workshop_v1.route("/<workshop_id>", methods=["PUT"])
@jwt_required
def update_workshop(workshop_id: str):
    """Update an existing workshop"""
    domain_id = get_current_domain_id()
    if not domain_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        update_data = WorkshopUpdateRequest.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = WorkshopController.update_workshop(db, str(domain_id), workshop_id, update_data)
        return jsonify(result), status_code
    finally:
        db.close()


@api_workshop_v1.route("/<workshop_id>", methods=["DELETE"])
@jwt_required
def delete_workshop(workshop_id: str):
    """Delete a workshop"""
    domain_id = get_current_domain_id()
    if not domain_id:
        return jsonify({"error": "Unauthorized"}), 401

    db: Session = next(get_db())
    try:
        result, status_code = WorkshopController.delete_workshop(db, str(domain_id), workshop_id)
        return jsonify(result), status_code
    finally:
        db.close()


@api_workshop_v1.route("/<workshop_id>/assign-to-project", methods=["POST"])
@jwt_required
def assign_to_project(workshop_id: str):
    """Assign workshop to project"""
    domain_id = get_current_domain_id()
    if not domain_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        assign_data = AssignToProjectRequest.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = WorkshopController.assign_to_project(
            db,
            str(domain_id),
            workshop_id,
            str(assign_data.project_id),
        )
        return jsonify(result), status_code
    finally:
        db.close()


@api_workshop_v1.route("/<workshop_id>/unassign-from-project", methods=["DELETE"])
@jwt_required
def unassign_from_project(workshop_id: str):
    """Remove workshop from its assigned project (link only, workshop remains)"""
    domain_id = get_current_domain_id()
    if not domain_id:
        return jsonify({"error": "Unauthorized"}), 401

    db: Session = next(get_db())
    try:
        result, status_code = WorkshopController.unassign_from_project(db, str(domain_id), workshop_id)
        return jsonify(result), status_code
    finally:
        db.close()


@api_workshop_v1.route("/<workshop_id>/export-to-sketch", methods=["POST"])
@jwt_required
def export_to_sketch(workshop_id: str):
    """Export workshop content to a new SongSketch"""
    user_id = get_current_user_id()
    domain_id = get_current_domain_id()
    if not user_id or not domain_id:
        return jsonify({"error": "Unauthorized"}), 401

    db: Session = next(get_db())
    try:
        result, status_code = WorkshopController.export_to_sketch(db, str(user_id), str(domain_id), workshop_id)
        return jsonify(result), status_code
    finally:
        db.close()
