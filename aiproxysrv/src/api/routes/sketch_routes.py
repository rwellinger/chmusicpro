"""API routes for sketch management"""

from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from sqlalchemy.orm import Session

from api.auth_middleware import jwt_required
from api.controllers.sketch_controller import SketchController
from db.database import get_db
from schemas.project_asset_schemas import AssignToProjectRequest
from schemas.sketch_schemas import SketchCreateRequest, SketchDuplicateRequest, SketchUpdateRequest


api_sketch_v1 = Blueprint("api_sketch_v1", __name__, url_prefix="/api/v1/sketches")


@api_sketch_v1.route("", methods=["POST"])
@jwt_required
def create_sketch():
    """Create a new sketch"""
    try:
        sketch_data = SketchCreateRequest.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = SketchController.create_sketch(db, sketch_data)
        return jsonify(result), status_code
    finally:
        db.close()


@api_sketch_v1.route("", methods=["GET"])
@jwt_required
def list_sketches():
    """Get list of sketches with pagination, search and filtering"""
    # Parse query parameters
    try:
        limit = int(request.args.get("limit", 20))
        offset = int(request.args.get("offset", 0))

        # Validate parameters
        if limit <= 0 or limit > 100:
            return jsonify({"error": "Limit must be between 1 and 100"}), 400
        if offset < 0:
            return jsonify({"error": "Offset must be >= 0"}), 400

    except ValueError:
        return jsonify({"error": "Invalid limit or offset parameter"}), 400

    # Parse search and sort parameters
    search = request.args.get("search", "").strip()
    workflow = request.args.get("workflow", None)  # Optional workflow filter
    sketch_type = request.args.get("sketch_type", None)  # Optional sketch type filter
    sort_by = request.args.get("sort_by", "created_at")
    sort_direction = request.args.get("sort_direction", "desc")

    # Validate sort parameters
    valid_sort_fields = ["created_at", "updated_at", "title"]
    if sort_by not in valid_sort_fields:
        return jsonify({"error": f"Invalid sort_by field. Must be one of: {valid_sort_fields}"}), 400

    if sort_direction not in ["asc", "desc"]:
        return jsonify({"error": "Invalid sort_direction. Must be 'asc' or 'desc'"}), 400

    # Validate workflow filter
    if workflow and workflow not in ["draft", "used", "archived"]:
        return jsonify({"error": "Invalid workflow. Must be one of: draft, used, archived"}), 400

    # Validate sketch_type filter
    if sketch_type and sketch_type not in ["song", "inspiration"]:
        return jsonify({"error": "Invalid sketch_type. Must be one of: song, inspiration"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = SketchController.get_sketches(
            db=db,
            limit=limit,
            offset=offset,
            search=search,
            workflow=workflow,
            sketch_type=sketch_type,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )
        return jsonify(result), status_code
    finally:
        db.close()


@api_sketch_v1.route("/<sketch_id>", methods=["GET"])
@jwt_required
def get_sketch(sketch_id: str):
    """Get a specific sketch by ID"""
    db: Session = next(get_db())
    try:
        result, status_code = SketchController.get_sketch_by_id(db, sketch_id)
        return jsonify(result), status_code
    finally:
        db.close()


@api_sketch_v1.route("/<sketch_id>", methods=["PUT"])
@jwt_required
def update_sketch(sketch_id: str):
    """Update an existing sketch"""
    try:
        update_data = SketchUpdateRequest.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = SketchController.update_sketch(db, sketch_id, update_data)
        return jsonify(result), status_code
    finally:
        db.close()


@api_sketch_v1.route("/<sketch_id>", methods=["DELETE"])
@jwt_required
def delete_sketch(sketch_id: str):
    """Delete a sketch"""
    db: Session = next(get_db())
    try:
        result, status_code = SketchController.delete_sketch(db, sketch_id)
        return jsonify(result), status_code
    finally:
        db.close()


@api_sketch_v1.route("/<sketch_id>/duplicate", methods=["POST"])
@jwt_required
def duplicate_sketch(sketch_id: str):
    """
    Duplicate a sketch (simple copy without translation)

    Body (optional):
    {
        "new_title_suffix": " (Copy 2)"  // Optional custom suffix
    }
    """
    try:
        # Parse request body (optional, defaults provided by schema)
        duplicate_data = SketchDuplicateRequest.model_validate(request.json or {})
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = SketchController.duplicate_sketch(db, sketch_id, duplicate_data)
        return jsonify(result), status_code
    finally:
        db.close()


@api_sketch_v1.route("/<sketch_id>/assign-to-project", methods=["POST"])
@jwt_required
def assign_to_project(sketch_id: str):
    """Assign sketch to project"""
    try:
        assign_data = AssignToProjectRequest.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = SketchController.assign_to_project(
            db, sketch_id, str(assign_data.project_id), str(assign_data.folder_id) if assign_data.folder_id else None
        )
        return jsonify(result), status_code
    finally:
        db.close()


@api_sketch_v1.route("/<sketch_id>/unassign-from-project", methods=["DELETE"])
@jwt_required
def unassign_from_project(sketch_id: str):
    """Remove sketch from its assigned project (link only, sketch remains)"""
    db: Session = next(get_db())
    try:
        result, status_code = SketchController.unassign_from_project(db, sketch_id)
        return jsonify(result), status_code
    finally:
        db.close()
