"""User API Key Orchestrator - Encrypt/decrypt/status for per-user API keys.

Follows Equipment pattern: uses encryption_service for Fernet encryption.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from business.encryption_service import encryption_service
from db.user_service import UserService
from utils.logger import logger


if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class UserApiKeyOrchestrator:
    """Orchestrates per-user API key management (encrypt, decrypt, status)."""

    def __init__(self):
        self.user_service = UserService()

    def save_api_keys(self, db: Session, user_id: str, keys: dict[str, str | None]) -> bool:
        """
        Encrypt and save API keys for a user.

        Args:
            db: Database session
            user_id: User UUID as string
            keys: Dict with plaintext keys. Valid keys:
                openai_api_key, openai_admin_api_key, claude_api_key
                None or empty string = clear that key

        Returns:
            True if successful, False otherwise
        """
        encrypted = {}
        key_mapping = {
            "openai_api_key": "openai_api_key_encrypted",
            "openai_admin_api_key": "openai_admin_api_key_encrypted",
            "claude_api_key": "claude_api_key_encrypted",
        }

        for plain_key, db_col in key_mapping.items():
            if plain_key in keys:
                value = keys[plain_key]
                if value and value.strip():
                    encrypted[db_col] = encryption_service.encrypt(value.strip())
                else:
                    encrypted[db_col] = None  # Clear the key

        if not encrypted:
            logger.debug("No API keys to update", user_id=user_id)
            return True

        logger.info("Saving API keys", user_id=user_id, keys_updated=list(encrypted.keys()))
        return self.user_service.update_api_keys(db, user_id, **encrypted)

    def get_api_key_status(self, db: Session, user_id: str) -> dict[str, bool]:
        """
        Get which API keys are configured for a user (boolean flags only).

        Args:
            db: Database session
            user_id: User UUID as string

        Returns:
            Dict with boolean flags for each key
        """
        raw = self.user_service.get_user_api_keys(db, user_id)
        if not raw:
            return {
                "has_openai_api_key": False,
                "has_openai_admin_api_key": False,
                "has_claude_api_key": False,
            }

        return {
            "has_openai_api_key": bool(raw.get("openai_api_key_encrypted")),
            "has_openai_admin_api_key": bool(raw.get("openai_admin_api_key_encrypted")),
            "has_claude_api_key": bool(raw.get("claude_api_key_encrypted")),
        }

    def get_decrypted_keys(self, db: Session, user_id: str) -> dict[str, str | None]:
        """
        Decrypt and return all API keys for a user.

        Used internally by the key injection middleware to load keys into flask.g.

        Args:
            db: Database session
            user_id: User UUID as string

        Returns:
            Dict with decrypted key values (or None if not set)
        """
        raw = self.user_service.get_user_api_keys(db, user_id)
        if not raw:
            return {
                "openai_api_key": None,
                "openai_admin_api_key": None,
                "claude_api_key": None,
            }

        return {
            "openai_api_key": encryption_service.decrypt(raw.get("openai_api_key_encrypted")),
            "openai_admin_api_key": encryption_service.decrypt(raw.get("openai_admin_api_key_encrypted")),
            "claude_api_key": encryption_service.decrypt(raw.get("claude_api_key_encrypted")),
        }

    def clear_all_api_keys(self, db: Session, user_id: str) -> bool:
        """
        Remove all API keys for a user.

        Args:
            db: Database session
            user_id: User UUID as string

        Returns:
            True if successful, False otherwise
        """
        logger.info("Clearing all API keys", user_id=user_id)
        return self.user_service.update_api_keys(
            db,
            user_id,
            openai_api_key_encrypted=None,
            openai_admin_api_key_encrypted=None,
            claude_api_key_encrypted=None,
        )


# Module-level instance
user_api_key_orchestrator = UserApiKeyOrchestrator()
