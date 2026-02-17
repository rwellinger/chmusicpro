"""
User Authentication and Management Routes
"""

from flask import Blueprint, jsonify, request
from flask_pydantic import validate

from api.auth_middleware import domain_role_required, get_current_user_id, jwt_required
from api.controllers.user_controller import UserController
from business.user_api_key_orchestrator import user_api_key_orchestrator
from db.database import SessionLocal
from db.models import DomainType
from schemas.user_schemas import (
    ApiKeyUpdateRequest,
    LoginRequest,
    PasswordChangeRequest,
    PasswordResetRequest,
    UserCreateRequest,
    UserUpdateRequest,
)


# Create blueprint
api_user_v1 = Blueprint("api_user_v1", __name__, url_prefix="/api/v1/user")

# Controller instance
user_controller = UserController()


@api_user_v1.route("/captcha", methods=["GET"])
def get_captcha():
    """Get a math CAPTCHA challenge (no auth required)"""
    try:
        response_data, status_code = user_controller.get_captcha_challenge()
        return jsonify(response_data), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_user_v1.route("/create", methods=["POST"])
@validate()
def create_user(body: UserCreateRequest):
    """Create a new user account with optional reCAPTCHA and auto-login"""
    try:
        remote_ip = request.remote_addr
        user_agent_str = request.headers.get("User-Agent")
        response_data, status_code = user_controller.create_user(body, remote_ip=remote_ip, user_agent=user_agent_str)
        return jsonify(response_data), status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_user_v1.route("/login", methods=["POST"])
@validate()
def login(body: LoginRequest):
    """Authenticate user and return JWT token"""
    try:
        response_data, status_code = user_controller.login(body)
        return jsonify(response_data), status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_user_v1.route("/logout", methods=["POST"])
@jwt_required
def logout():
    """Logout user (requires JWT, frontend handles token removal)"""
    try:
        response_data, status_code = user_controller.logout()
        return jsonify(response_data), status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_user_v1.route("/profile", methods=["GET"])
@jwt_required
def get_user_profile():
    """Get user profile (uses JWT token for user ID)"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"success": False, "error": "User ID not found in token"}), 401

        response_data, status_code = user_controller.get_user_profile(str(user_id))
        return jsonify(response_data), status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_user_v1.route("/edit", methods=["PUT"])
@jwt_required
@validate()
def update_user(body: UserUpdateRequest):
    """Update user information (uses JWT token for user ID)"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"success": False, "error": "User ID not found in token"}), 401

        response_data, status_code = user_controller.update_user(str(user_id), body)
        return jsonify(response_data), status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_user_v1.route("/password", methods=["PUT"])
@jwt_required
@validate()
def change_password(body: PasswordChangeRequest):
    """Change user password (uses JWT token for user ID)"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"success": False, "error": "User ID not found in token"}), 401

        response_data, status_code = user_controller.change_password(str(user_id), body)
        return jsonify(response_data), status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_user_v1.route("/password-reset", methods=["POST"])
@jwt_required
@domain_role_required("admin", "owner", domain_type=DomainType.SYSTEM)
@validate()
def reset_password(body: PasswordResetRequest):
    """Reset user password (admin function, requires JWT + admin role)"""
    try:
        response_data, status_code = user_controller.reset_password(body)
        return jsonify(response_data), status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_user_v1.route("/list", methods=["GET"])
@jwt_required
@domain_role_required("admin", "owner", domain_type=DomainType.SYSTEM)
def list_users():
    """List all users (admin function, requires JWT + admin role)"""
    try:
        # Get pagination parameters
        skip = int(request.args.get("skip", 0))
        limit = int(request.args.get("limit", 100))

        response_data, status_code = user_controller.list_users(skip, limit)
        return jsonify(response_data), status_code
    except ValueError:
        return jsonify({"success": False, "error": "Invalid pagination parameters"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_user_v1.route("/validate-token", methods=["POST"])
def validate_token():
    """Validate JWT token with database check"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "error": "Missing or invalid authorization header"}), 401

        token = auth_header.split(" ")[1]
        user_info = user_controller.validate_token(token)

        if user_info:
            return jsonify(
                {"success": True, "valid": True, "user_id": user_info["user_id"], "email": user_info["email"]}
            ), 200
        else:
            return jsonify({"success": False, "valid": False, "error": "Invalid or expired token"}), 401

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_user_v1.route("/validate-token-light", methods=["POST"])
def validate_token_light():
    """Lightweight JWT token validation (no database check)"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "error": "Missing or invalid authorization header"}), 401

        token = auth_header.split(" ")[1]
        user_info = user_controller.validate_token_light(token)

        if user_info:
            return jsonify(
                {"success": True, "valid": True, "user_id": user_info["user_id"], "email": user_info["email"]}
            ), 200
        else:
            return jsonify({"success": False, "valid": False, "error": "Invalid or expired token"}), 401

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_user_v1.route("/api-keys", methods=["PUT"])
@jwt_required
@validate()
def update_api_keys(body: ApiKeyUpdateRequest):
    """Save/update user API keys (encrypted)"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"success": False, "error": "User ID not found in token"}), 401

        with SessionLocal() as db:
            keys = body.model_dump(exclude_none=True)
            success = user_api_key_orchestrator.save_api_keys(db, str(user_id), keys)

            if not success:
                return jsonify({"success": False, "error": "Failed to update API keys"}), 500

            status = user_api_key_orchestrator.get_api_key_status(db, str(user_id))
            return jsonify({"success": True, "message": "API keys updated", **status}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_user_v1.route("/api-keys/status", methods=["GET"])
@jwt_required
def get_api_key_status():
    """Get which API keys are configured (booleans only, never actual keys)"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"success": False, "error": "User ID not found in token"}), 401

        with SessionLocal() as db:
            status = user_api_key_orchestrator.get_api_key_status(db, str(user_id))
            return jsonify({"success": True, **status}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_user_v1.route("/api-keys", methods=["DELETE"])
@jwt_required
def delete_api_keys():
    """Remove all API keys"""
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"success": False, "error": "User ID not found in token"}), 401

        with SessionLocal() as db:
            success = user_api_key_orchestrator.clear_all_api_keys(db, str(user_id))

            if not success:
                return jsonify({"success": False, "error": "Failed to delete API keys"}), 500

            return jsonify({"success": True, "message": "All API keys removed"}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
