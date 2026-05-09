"""Central AI configuration logic for multi-provider support.

Determines which AI providers are available based on .env configuration.
Used by adapters and routes to decide provider routing.
"""

from config.settings import (
    AGENT_EXTERNAL_MODEL_CLAUDE,
    AGENT_EXTERNAL_MODEL_OPENAI,
    AGENT_EXTERNAL_PROVIDER,
    APPLICATION_MODE,
)


# AI Provider constants
PROVIDER_OPENAI = "openai"
PROVIDER_CLAUDE = "claude"

VALID_PROVIDERS = {PROVIDER_OPENAI, PROVIDER_CLAUDE}
EXTERNAL_PROVIDERS = {PROVIDER_OPENAI, PROVIDER_CLAUDE}

# Application Mode constants
APP_MODE_PROFI = "PROFI"
APP_MODE_LIGHT = "LIGHT"
APP_MODE_PRJCT = "PRJCT"

VALID_APP_MODES = {APP_MODE_PROFI, APP_MODE_LIGHT, APP_MODE_PRJCT}


class AIConfig:
    """Central AI configuration with static methods."""

    @staticmethod
    def get_external_provider() -> str:
        """Get configured external provider name."""
        provider = AGENT_EXTERNAL_PROVIDER.lower().strip()
        if provider not in EXTERNAL_PROVIDERS:
            return PROVIDER_OPENAI
        return provider

    @staticmethod
    def get_external_model() -> str:
        """Get default model for the configured external provider."""
        provider = AIConfig.get_external_provider()
        if provider == PROVIDER_CLAUDE:
            return AGENT_EXTERNAL_MODEL_CLAUDE
        return AGENT_EXTERNAL_MODEL_OPENAI

    @staticmethod
    def get_available_providers() -> list[str]:
        """Get list of available provider names."""
        return [AIConfig.get_external_provider()]

    @staticmethod
    def get_application_mode() -> str:
        """Get current application mode (PROFI/LIGHT/PRJCT)."""
        mode = APPLICATION_MODE.upper().strip()
        if mode not in VALID_APP_MODES:
            return APP_MODE_PROFI
        return mode

    @staticmethod
    def validate_provider(provider: str) -> bool:
        """Check if a provider is valid and currently available."""
        return provider in VALID_PROVIDERS
