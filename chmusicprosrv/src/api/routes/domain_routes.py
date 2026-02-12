"""API routes for domain management"""

from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from sqlalchemy.orm import Session

from api.auth_middleware import domain_role_required, get_current_user_id, jwt_required
from api.controllers.domain_controller import DomainController
from db.database import get_db
from db.models import DomainType
from schemas.domain_schemas import (
    DomainCreateRequest,
    DomainMemberAddRequest,
    DomainMemberUpdateRequest,
    DomainSwitchRequest,
    DomainUpdateRequest,
)


api_domain_v1 = Blueprint("api_domain_v1", __name__, url_prefix="/api/v1/domains")


@api_domain_v1.route("", methods=["GET"])
@jwt_required
def list_domains():
    """List all domains for the current user"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    db: Session = next(get_db())
    try:
        result, status_code = DomainController.list_user_domains(db, str(user_id))
        return jsonify(result), status_code
    finally:
        db.close()


@api_domain_v1.route("/<domain_id>", methods=["GET"])
@jwt_required
def get_domain(domain_id: str):
    """Get domain detail"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    db: Session = next(get_db())
    try:
        result, status_code = DomainController.get_domain_detail(db, domain_id, str(user_id))
        return jsonify(result), status_code
    finally:
        db.close()


@api_domain_v1.route("", methods=["POST"])
@jwt_required
@domain_role_required("admin", "owner", domain_type=DomainType.SYSTEM)
def create_domain():
    """Create a new domain (system admin only)"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = DomainCreateRequest.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = DomainController.create_domain(db, str(user_id), data)
        if status_code < 300:
            db.commit()
        return jsonify(result), status_code
    finally:
        db.close()


@api_domain_v1.route("/<domain_id>", methods=["PUT"])
@jwt_required
def update_domain(domain_id: str):
    """Update a domain (permission check in controller)"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = DomainUpdateRequest.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = DomainController.update_domain(db, domain_id, str(user_id), data)
        if status_code < 300:
            db.commit()
        return jsonify(result), status_code
    finally:
        db.close()


@api_domain_v1.route("/<domain_id>", methods=["DELETE"])
@jwt_required
@domain_role_required("admin", "owner", domain_type=DomainType.SYSTEM)
def deactivate_domain(domain_id: str):
    """Deactivate a domain (system admin only)"""
    db: Session = next(get_db())
    try:
        result, status_code = DomainController.deactivate_domain(db, domain_id)
        if status_code < 300:
            db.commit()
        return jsonify(result), status_code
    finally:
        db.close()


@api_domain_v1.route("/switch", methods=["POST"])
@jwt_required
def switch_domain():
    """Switch the active domain"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = DomainSwitchRequest.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = DomainController.switch_domain(db, str(user_id), data)
        if status_code < 300:
            db.commit()
        return jsonify(result), status_code
    finally:
        db.close()


@api_domain_v1.route("/<domain_id>/members", methods=["GET"])
@jwt_required
def list_members(domain_id: str):
    """List members of a domain (permission check in controller)"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    db: Session = next(get_db())
    try:
        result, status_code = DomainController.list_domain_members(db, domain_id, str(user_id))
        return jsonify(result), status_code
    finally:
        db.close()


@api_domain_v1.route("/<domain_id>/members", methods=["POST"])
@jwt_required
def add_member(domain_id: str):
    """Add a member to a domain (permission check in controller)"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = DomainMemberAddRequest.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = DomainController.add_domain_member(db, domain_id, str(user_id), data)
        if status_code < 300:
            db.commit()
        return jsonify(result), status_code
    finally:
        db.close()


@api_domain_v1.route("/<domain_id>/members/<target_user_id>", methods=["PUT"])
@jwt_required
def update_member(domain_id: str, target_user_id: str):
    """Update a member's role (permission check in controller)"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = DomainMemberUpdateRequest.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = DomainController.update_domain_member(db, domain_id, target_user_id, data, str(user_id))
        if status_code < 300:
            db.commit()
        return jsonify(result), status_code
    finally:
        db.close()


@api_domain_v1.route("/<domain_id>/members/<target_user_id>", methods=["DELETE"])
@jwt_required
def remove_member(domain_id: str, target_user_id: str):
    """Remove a member from a domain (permission check in controller)"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    db: Session = next(get_db())
    try:
        result, status_code = DomainController.remove_domain_member(db, domain_id, target_user_id, str(user_id))
        if status_code < 300:
            db.commit()
        return jsonify(result), status_code
    finally:
        db.close()
