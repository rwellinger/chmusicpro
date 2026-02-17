"""
Config Routes - Application configuration endpoints
"""

from pathlib import Path

from flask import Blueprint, jsonify

from api.auth_middleware import jwt_required
from config.settings import CHMUSICPRO_IGNORE_FILE
from utils.logger import logger


api_config_v1 = Blueprint("api_config_v1", __name__, url_prefix="/api/v1/config")


@api_config_v1.route("/ignore-patterns", methods=["GET"])
@jwt_required
def get_ignore_patterns():
    """
    Return ignore patterns from .chmusicproignore file.
    Used by frontend Mirror Sync to filter files before upload.
    """
    ignore_file = Path(CHMUSICPRO_IGNORE_FILE)

    if not ignore_file.exists():
        logger.warning("Ignore file not found", path=str(ignore_file))
        return jsonify({"data": {"patterns": []}}), 200

    try:
        content = ignore_file.read_text(encoding="utf-8")
        patterns = []
        for line in content.splitlines():
            stripped = line.strip()
            # Skip empty lines and comments
            if stripped and not stripped.startswith("#"):
                patterns.append(stripped)

        return jsonify({"data": {"patterns": patterns}}), 200
    except Exception as e:
        logger.error("Failed to read ignore file", path=str(ignore_file), error=str(e))
        return jsonify({"data": {"patterns": []}}), 200
