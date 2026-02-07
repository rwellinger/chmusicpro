"""Ollama Orchestrator - Coordinates Ollama model operations (NOT testable, orchestration only)."""

from typing import Any

from adapters.ollama.api_client import OllamaAPIClient, OllamaAPIError
from business.ollama_model_transformer import OllamaModelTransformer
from config.settings import OLLAMA_CHAT_MODELS, OLLAMA_DEFAULT_MODEL
from utils.logger import logger


class OllamaOrchestrator:
    """Orchestrator for Ollama model operations (coordinates services, NO business logic)."""

    def __init__(self):
        self.api_client = OllamaAPIClient()

    def get_models(self) -> tuple[dict[str, Any], int]:
        """
        Get available Ollama models (raw response from server).

        Orchestrates: API client only (no transformation)

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            data = self.api_client.get_tags()
            return data, 200

        except OllamaAPIError as e:
            error_msg = str(e)
            if "timeout" in error_msg.lower():
                return {"error": error_msg}, 504
            elif "connect" in error_msg.lower():
                return {"error": error_msg}, 503
            else:
                return {"error": error_msg}, 500

        except Exception as e:
            logger.error("Unexpected error in get_models", error=str(e), error_type=type(e).__name__)
            return {"error": f"Unexpected error: {str(e)}"}, 500

    def get_available_chat_models(self) -> tuple[dict[str, Any], int]:
        """
        Get available Ollama chat models based on configuration.

        Orchestrates: API client + Transformer
        - OLLAMA_CHAT_MODELS empty: Fetch all models from server (dynamic)
        - OLLAMA_CHAT_MODELS set: Return only whitelisted models (static)

        Returns:
            Tuple of (response_data, status_code)
            Response format: {"models": [{"name": str, "context_window": int, "is_default": bool}]}
        """
        try:
            # Business Logic: Parse configured models using transformer
            configured_models = OllamaModelTransformer.parse_configured_models(OLLAMA_CHAT_MODELS)

            if configured_models:
                # Static mode: Use whitelist from configuration
                logger.info("Using static Ollama model list", model_count=len(configured_models))

                # Business Logic: Build static model list using transformer
                models = OllamaModelTransformer.build_static_model_list(configured_models, OLLAMA_DEFAULT_MODEL)

            else:
                # Dynamic mode: Fetch all models from Ollama server
                logger.info("Fetching dynamic Ollama model list from server")

                # Call API client
                data = self.api_client.get_tags()
                server_models = data.get("models", [])

                # Business Logic: Transform server models using transformer
                models = OllamaModelTransformer.transform_server_models_to_frontend(server_models, OLLAMA_DEFAULT_MODEL)

                logger.info("Ollama models fetched and transformed", model_count=len(models))

            return {"models": models}, 200

        except OllamaAPIError as e:
            error_msg = str(e)
            if "timeout" in error_msg.lower():
                return {"error": error_msg}, 504
            elif "connect" in error_msg.lower():
                return {"error": error_msg}, 503
            else:
                return {"error": error_msg}, 500

        except Exception as e:
            logger.error("Unexpected error in get_available_chat_models", error=str(e), error_type=type(e).__name__)
            return {"error": f"Unexpected error: {str(e)}"}, 500
