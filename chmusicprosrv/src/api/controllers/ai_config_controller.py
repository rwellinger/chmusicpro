"""AI Config Controller - Exposes AI configuration to frontend (Controller layer)."""

from typing import Any

from config.ai_config import AIConfig


class AIConfigController:
    """Controller for AI configuration endpoint."""

    def get_config(self) -> dict[str, Any]:
        """Return current AI configuration for frontend consumption."""
        config = {
            "mode": AIConfig.get_mode(),
            "available_providers": AIConfig.get_available_providers(),
            "ollama_enabled": AIConfig.is_ollama_enabled(),
            "external_enabled": AIConfig.is_external_enabled(),
            "application_mode": AIConfig.get_application_mode(),
        }

        if AIConfig.is_external_enabled():
            config["external_provider"] = AIConfig.get_external_provider()
            config["external_model"] = AIConfig.get_external_model()

        return config
