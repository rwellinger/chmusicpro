"""
Health Check Routes - System health monitoring endpoints
"""

from flask import Blueprint, jsonify

from api.auth_middleware import jwt_required
from infrastructure.storage.s3_storage import S3Storage
from utils.logger import logger


# Create blueprint
api_health_v1 = Blueprint("api_health_v1", __name__, url_prefix="/api/v1/health")


@api_health_v1.route("/storage", methods=["GET"])
@jwt_required
def check_storage():
    """
    Check S3 storage backend health (MinIO/AWS S3)

    Quick health check with 2s timeout to detect if storage backend is reachable.
    Used by CLI tools (aiproxy-cli) before upload/mirror operations to fail-fast
    instead of waiting for long timeouts.

    Response:
        200: {'status': 'healthy', 'message': 'OK'}
        503: {'status': 'unhealthy', 'message': 'Cannot reach storage backend at http://...'}

    Example:
        GET /api/v1/health/storage
        Headers: Authorization: Bearer <JWT_TOKEN>

    CLI Usage:
        aiproxy-cli checks this endpoint before upload/mirror to prevent:
        - Long timeout waits (600s per batch)
        - User confusion (seeing "success" but nothing uploaded)
        - Inconsistent state (DB records without S3 files)
    """
    try:
        storage = S3Storage()
        is_healthy, message = storage.health_check(timeout=2)

        if is_healthy:
            logger.debug("Storage health check: healthy")
            return jsonify({"status": "healthy", "message": message}), 200
        else:
            logger.warning("Storage health check: unhealthy", message=message)
            return jsonify({"status": "unhealthy", "message": message}), 503

    except Exception as e:
        error_msg = f"Health check failed: {str(e)}"
        logger.error("Storage health check error", error=str(e), error_type=type(e).__name__)
        return jsonify({"status": "unhealthy", "message": error_msg}), 503
