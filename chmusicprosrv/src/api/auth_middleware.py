"""
JWT Authentication Middleware for Flask API
"""

from functools import wraps

from flask import g, jsonify, request

from business.user_auth_service import UserAuthService
from db.user_service import UserService
from utils.logger import logger


def jwt_required(f):
    """
    Decorator to require JWT authentication for API endpoints.
    Sets g.current_user_id, g.current_user_email, g.current_domain_id, g.current_domain_role.
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
            g.current_user_role = user.role

            # Set domain info from JWT (backwards compat: resolve from DB if missing)
            active_domain_id = payload.get("active_domain_id")
            domain_role = payload.get("domain_role")

            if not active_domain_id:
                # Old JWT without domain info - look up default domain
                from db.domain_service import DomainService

                domain_svc = DomainService()
                default_domain = domain_svc.get_default_domain_for_user(db, payload.get("user_id"))
                if default_domain:
                    active_domain_id = str(default_domain.id)
                    domain_role = domain_svc.get_user_role_in_domain(db, str(default_domain.id), payload.get("user_id"))
                    logger.debug(
                        "Domain resolved from DB (old JWT)",
                        user_id=payload.get("user_id"),
                        domain_id=active_domain_id,
                    )

            g.current_domain_id = active_domain_id
            g.current_domain_role = domain_role

            return f(*args, **kwargs)
        finally:
            # Always close the database connection to prevent pool exhaustion
            db.close()

    return decorated_function


def admin_required(f):
    """
    Decorator to require admin role for API endpoints.
    Must be used AFTER @jwt_required (which sets g.current_user_role).
    Returns 403 if user is not an admin.

    Note: This is the legacy decorator. For domain-based access control,
    use domain_role_required() instead. Kept for backwards compatibility
    during Phase 1 transition.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, "current_user_role") or g.current_user_role != "admin":
            return jsonify({"success": False, "error": "Admin access required"}), 403
        return f(*args, **kwargs)

    return decorated_function


def domain_role_required(*allowed_roles):
    """
    Decorator to require specific domain roles for API endpoints.
    Must be used AFTER @jwt_required (which sets g.current_domain_role).
    Returns 403 if user's domain role is not in allowed_roles.

    Usage:
        @api.route("/admin-action")
        @jwt_required
        @domain_role_required("owner", "admin")
        def admin_action():
            ...
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            domain_role = getattr(g, "current_domain_role", None)
            if domain_role not in allowed_roles:
                return jsonify({"success": False, "error": "Insufficient domain permissions"}), 403
            return f(*args, **kwargs)

        return decorated_function

    return decorator


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


def get_current_user_role():
    """
    Helper function to get current authenticated user role from Flask g object.
    Returns role string or None if not authenticated.
    """
    if hasattr(g, "current_user_role"):
        return g.current_user_role
    return None


def get_current_domain_id():
    """
    Helper function to get current active domain ID from Flask g object.
    Returns domain_id (UUID string) or None if not set.
    """
    if hasattr(g, "current_domain_id"):
        return g.current_domain_id
    return None


def get_current_domain_role():
    """
    Helper function to get current domain role from Flask g object.
    Returns domain role string or None if not set.
    """
    if hasattr(g, "current_domain_role"):
        return g.current_domain_role
    return None
