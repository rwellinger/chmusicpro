"""AI Config Controller - Exposes AI configuration to frontend (Controller layer)."""

from typing import Any

from config.ai_config import AIConfig


class AIConfigController:
    """Controller for AI configuration endpoint."""

    def get_config(self) -> dict[str, Any]:
        """Return current AI configuration for frontend consumption."""
        # Frontend keeps `mode`/`ollama_enabled`/`external_enabled` for backwards compat,
        # but only external providers (OpenAI/Claude) are supported now.
        return {
            "mode": "external",
            "available_providers": AIConfig.get_available_providers(),
            "ollama_enabled": False,
            "external_enabled": True,
            "application_mode": AIConfig.get_application_mode(),
            "external_provider": AIConfig.get_external_provider(),
            "external_model": AIConfig.get_external_model(),
        }
