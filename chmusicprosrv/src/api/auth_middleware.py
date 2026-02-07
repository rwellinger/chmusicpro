"""
JWT Authentication Middleware for Flask API
"""

from functools import wraps

from flask import g, jsonify, request

from business.user_auth_service import UserAuthService
from db.user_service import UserService


def jwt_required(f):
    """
    Decorator to require JWT authentication for API endpoints.
    Sets g.current_user_id and g.current_user_email if token is valid.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get Authorization header
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"success": False, "error": "Authorization header is required"}), 401

        # Check Bearer token format
        try:
            bearer, token = auth_header.split(" ")
            if bearer.lower() != "bearer":
                raise ValueError("Invalid authorization header format")
        except ValueError:
            return jsonify({"success": False, "error": "Authorization header must be in format 'Bearer <token>'"}), 401

        # Validate JWT token
        auth_service = UserAuthService()
        payload = auth_service.verify_jwt_token(token)

        # User service for DB operations
        user_service = UserService()

        if not payload:
            return jsonify({"success": False, "error": "Invalid or expired token"}), 401

        # Verify user still exists in database (prevents phantom users after DB restore)
        from db.database import get_db

        db = next(get_db())
        try:
            user = user_service.get_user_by_id(db, payload.get("user_id"))

            if not user:
                return jsonify({"success": False, "error": "User no longer exists. Please log in again."}), 401

            # Set user info in Flask's g object for use in route handlers
            g.current_user_id = payload.get("user_id")
            g.current_user_email = payload.get("email")

            return f(*args, **kwargs)
        finally:
            # Always close the database connection to prevent pool exhaustion
            db.close()

    return decorated_function


def get_current_user():
    """
    Helper function to get current authenticated user info from Flask g object.
    Returns dict with user_id and email, or None if not authenticated.
    """
    if hasattr(g, "current_user_id") and hasattr(g, "current_user_email"):
        return {"user_id": g.current_user_id, "email": g.current_user_email}
    return None


def get_current_user_id():
    """
    Helper function to get current authenticated user ID from Flask g object.
    Returns user_id (UUID) or None if not authenticated.
    """
    if hasattr(g, "current_user_id"):
        return g.current_user_id
    return None
