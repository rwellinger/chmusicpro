"""API routes for suno template management"""

from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from sqlalchemy.orm import Session

from api.auth_middleware import get_current_domain_id, get_current_user_id, jwt_required
from api.controllers.suno_template_controller import SunoTemplateController
from db.database import get_db
from schemas.project_asset_schemas import AssignToProjectRequest
from schemas.suno_template_schemas import SunoTemplateCreateRequest, SunoTemplateUpdateRequest


api_suno_template_v1 = Blueprint("api_suno_template_v1", __name__, url_prefix="/api/v1/suno-templates")


@api_suno_template_v1.route("", methods=["POST"])
@jwt_required
def create_template():
    """Create a new suno template"""
    user_id = get_current_user_id()
    domain_id = get_current_domain_id()
    if not user_id or not domain_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        template_data = SunoTemplateCreateRequest.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = SunoTemplateController.create_template(db, str(user_id), str(domain_id), template_data)
        return jsonify(result), status_code
    finally:
        db.close()


@api_suno_template_v1.route("", methods=["GET"])
@jwt_required
def list_templates():
    """Get list of suno templates with pagination, search and filtering"""
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
    template_type = request.args.get("template_type", None)
    sort_by = request.args.get("sort_by", "created_at")
    sort_direction = request.args.get("sort_direction", "desc")

    valid_sort_fields = ["created_at", "updated_at", "title"]
    if sort_by not in valid_sort_fields:
        return jsonify({"error": f"Invalid sort_by field. Must be one of: {valid_sort_fields}"}), 400

    if sort_direction not in ["asc", "desc"]:
        return jsonify({"error": "Invalid sort_direction. Must be 'asc' or 'desc'"}), 400

    if template_type and template_type not in ["song", "instrumental"]:
        return jsonify({"error": "Invalid template_type. Must be one of: song, instrumental"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = SunoTemplateController.get_templates(
            db=db,
            domain_id=str(domain_id),
            limit=limit,
            offset=offset,
            search=search,
            template_type=template_type,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )
        return jsonify(result), status_code
    finally:
        db.close()


@api_suno_template_v1.route("/<template_id>", methods=["GET"])
@jwt_required
def get_template(template_id: str):
    """Get a specific suno template by ID"""
    domain_id = get_current_domain_id()
    if not domain_id:
        return jsonify({"error": "Unauthorized"}), 401

    db: Session = next(get_db())
    try:
        result, status_code = SunoTemplateController.get_template_by_id(db, str(domain_id), template_id)
        return jsonify(result), status_code
    finally:
        db.close()


@api_suno_template_v1.route("/<template_id>", methods=["PUT"])
@jwt_required
def update_template(template_id: str):
    """Update an existing suno template"""
    domain_id = get_current_domain_id()
    if not domain_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        update_data = SunoTemplateUpdateRequest.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = SunoTemplateController.update_template(db, str(domain_id), template_id, update_data)
        return jsonify(result), status_code
    finally:
        db.close()


@api_suno_template_v1.route("/<template_id>", methods=["DELETE"])
@jwt_required
def delete_template(template_id: str):
    """Delete a suno template"""
    domain_id = get_current_domain_id()
    if not domain_id:
        return jsonify({"error": "Unauthorized"}), 401

    db: Session = next(get_db())
    try:
        result, status_code = SunoTemplateController.delete_template(db, str(domain_id), template_id)
        return jsonify(result), status_code
    finally:
        db.close()


@api_suno_template_v1.route("/from-sketch/<sketch_id>", methods=["POST"])
@jwt_required
def create_from_sketch(sketch_id: str):
    """Create a suno template from an existing sketch (Song-Modus)"""
    user_id = get_current_user_id()
    domain_id = get_current_domain_id()
    if not user_id or not domain_id:
        return jsonify({"error": "Unauthorized"}), 401

    db: Session = next(get_db())
    try:
        result, status_code = SunoTemplateController.create_from_sketch(db, str(user_id), str(domain_id), sketch_id)
        return jsonify(result), status_code
    finally:
        db.close()


@api_suno_template_v1.route("/<template_id>/assign-to-project", methods=["POST"])
@jwt_required
def assign_to_project(template_id: str):
    """Assign suno template to project"""
    domain_id = get_current_domain_id()
    if not domain_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        assign_data = AssignToProjectRequest.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = SunoTemplateController.assign_to_project(
            db,
            str(domain_id),
            template_id,
            str(assign_data.project_id),
            str(assign_data.folder_id) if assign_data.folder_id else None,
        )
        return jsonify(result), status_code
    finally:
        db.close()


@api_suno_template_v1.route("/<template_id>/unassign-from-project", methods=["DELETE"])
@jwt_required
def unassign_from_project(template_id: str):
    """Remove suno template from its assigned project"""
    domain_id = get_current_domain_id()
    if not domain_id:
        return jsonify({"error": "Unauthorized"}), 401

    db: Session = next(get_db())
    try:
        result, status_code = SunoTemplateController.unassign_from_project(db, str(domain_id), template_id)
        return jsonify(result), status_code
    finally:
        db.close()
