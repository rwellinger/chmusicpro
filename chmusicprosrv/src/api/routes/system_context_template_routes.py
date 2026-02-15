"""API routes for system context template management"""

from uuid import UUID

from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from sqlalchemy.orm import Session

from api.auth_middleware import domain_role_required, jwt_required
from api.controllers.system_context_template_controller import SystemContextTemplateController
from db.database import get_db
from db.models import DomainType
from schemas.system_context_template_schemas import SystemContextTemplateCreate, SystemContextTemplateUpdate


api_system_context_template_v1 = Blueprint(
    "api_system_context_template_v1", __name__, url_prefix="/api/v1/system-context-templates"
)

controller = SystemContextTemplateController()


@api_system_context_template_v1.route("", methods=["GET"])
@jwt_required
@domain_role_required("admin", "owner", domain_type=DomainType.KI_TEMPLATES)
def get_all_templates():
    """Get all system context templates (admin)"""
    db: Session = next(get_db())
    try:
        result, status_code = controller.get_all_templates(db)
        return jsonify(result), status_code
    finally:
        db.close()


@api_system_context_template_v1.route("/active", methods=["GET"])
@jwt_required
def get_active_templates():
    """Get active system context templates (any authenticated user, for chat dropdown)"""
    db: Session = next(get_db())
    try:
        result, status_code = controller.get_active_templates(db)
        return jsonify(result), status_code
    finally:
        db.close()


@api_system_context_template_v1.route("/<uuid:template_id>", methods=["GET"])
@jwt_required
@domain_role_required("admin", "owner", domain_type=DomainType.KI_TEMPLATES)
def get_template_by_id(template_id: UUID):
    """Get a specific template by ID (admin)"""
    db: Session = next(get_db())
    try:
        result, status_code = controller.get_template_by_id(db, template_id)
        return jsonify(result), status_code
    finally:
        db.close()


@api_system_context_template_v1.route("", methods=["POST"])
@jwt_required
@domain_role_required("admin", "owner", domain_type=DomainType.KI_TEMPLATES)
def create_template():
    """Create a new system context template (admin)"""
    try:
        template_data = SystemContextTemplateCreate.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = controller.create_template(db, template_data)
        return jsonify(result), status_code
    finally:
        db.close()


@api_system_context_template_v1.route("/<uuid:template_id>", methods=["PUT"])
@jwt_required
@domain_role_required("admin", "owner", domain_type=DomainType.KI_TEMPLATES)
def update_template(template_id: UUID):
    """Update an existing system context template (admin)"""
    try:
        update_data = SystemContextTemplateUpdate.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = controller.update_template(db, template_id, update_data)
        return jsonify(result), status_code
    finally:
        db.close()


@api_system_context_template_v1.route("/<uuid:template_id>", methods=["DELETE"])
@jwt_required
@domain_role_required("admin", "owner", domain_type=DomainType.KI_TEMPLATES)
def delete_template(template_id: UUID):
    """Delete a system context template (admin)"""
    db: Session = next(get_db())
    try:
        result, status_code = controller.delete_template(db, template_id)
        return jsonify(result), status_code
    finally:
        db.close()
