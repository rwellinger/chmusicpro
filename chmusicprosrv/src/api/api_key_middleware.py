"""API Key Middleware - Load per-user API keys into flask.g for AI routes.

Usage in routes:
    from api.api_key_middleware import load_user_api_keys, require_api_key

    @route("/my-endpoint", methods=["POST"])
    @jwt_required
    def my_endpoint():
        load_user_api_keys()
        error = require_api_key("openai")
        if error:
            return jsonify(error[0]), error[1]
        ...
"""

from flask import g

from api.auth_middleware import get_current_user_id
from business.user_api_key_orchestrator import user_api_key_orchestrator
from db.database import SessionLocal
from utils.logger import logger


def load_user_api_keys():
    """Load user's decrypted API keys from DB into flask.g.

    Sets:
        g.user_openai_api_key
        g.user_openai_admin_api_key
        g.user_claude_api_key
    """
    user_id = get_current_user_id()
    if not user_id:
        return

    try:
        with SessionLocal() as db:
            keys = user_api_key_orchestrator.get_decrypted_keys(db, str(user_id))
            g.user_openai_api_key = keys.get("openai_api_key")
            g.user_openai_admin_api_key = keys.get("openai_admin_api_key")
            g.user_claude_api_key = keys.get("claude_api_key")
    except Exception as e:
        logger.error("Failed to load user API keys", user_id=str(user_id), error=str(e))
        g.user_openai_api_key = None
        g.user_openai_admin_api_key = None
        g.user_claude_api_key = None


def require_api_key(provider: str):
    """Check that user has the required API key configured.

    Args:
        provider: One of "openai", "openai_admin", "claude"

    Returns:
        Tuple of (error_dict, status_code) if key missing, or None if key present.
    """
    key_map = {
        "openai": getattr(g, "user_openai_api_key", None),
        "openai_admin": getattr(g, "user_openai_admin_api_key", None),
        "claude": getattr(g, "user_claude_api_key", None),
    }
    provider_labels = {
        "openai": "OpenAI",
        "openai_admin": "OpenAI Admin",
        "claude": "Claude",
    }
    if not key_map.get(provider):
        label = provider_labels.get(provider, provider)
        return {
            "error": f"{label} API key is not configured. Please add it in your profile settings.",
            "error_code": "missing_api_key",
            "provider": provider,
        }, 403
    return None
