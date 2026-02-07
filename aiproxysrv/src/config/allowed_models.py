"""Single source of truth for allowed AI models.

This module defines all allowed model lists for different AI providers.
Models can be configured via .env file or use defaults.
"""

from config.settings import OLLAMA_ALLOWED_MODELS as _OLLAMA_MODELS_RAW


# Ollama Models (configured via .env OLLAMA_ALLOWED_MODELS, comma-separated)
# Used for template-based generation, chat, compression
OLLAMA_ALLOWED_MODELS = [m.strip() for m in _OLLAMA_MODELS_RAW.split(",") if m.strip()]
