"""Ollama Model Transformer - Pure transformation functions for Ollama model data

Business Layer - Pure functions (100% testable, no side effects)
"""

from typing import Any

from config.model_context_windows import get_context_window_size


class OllamaModelTransformer:
    """
    Pure business logic for Ollama model transformations.

    All methods are static and pure functions (100% testable without mocks).
    """

    @staticmethod
    def parse_configured_models(model_config_string: str) -> list[str]:
        """
        Parse configured model names from comma-separated string.

        Pure function - no side effects, fully unit-testable

        Args:
            model_config_string: Comma-separated model names (e.g., "llama3.2:3b, qwen2.5:7b")
                                 Empty string returns empty list

        Returns:
            List of trimmed model names (duplicates removed, order preserved)

        Example:
            parse_configured_models("llama3.2:3b, qwen2.5:7b") -> ["llama3.2:3b", "qwen2.5:7b"]
            parse_configured_models("  model1,  ,model2  ") -> ["model1", "model2"]
            parse_configured_models("") -> []
        """
        if not model_config_string or not model_config_string.strip():
            return []

        # Split, strip, filter empty, preserve order, remove duplicates
        models = []
        seen = set()
        for model in model_config_string.split(","):
            model_stripped = model.strip()
            if model_stripped and model_stripped not in seen:
                models.append(model_stripped)
                seen.add(model_stripped)

        return models

    @staticmethod
    def transform_server_model_to_frontend(server_model: dict[str, Any], default_model: str) -> dict[str, Any] | None:
        """
        Transform Ollama server model to frontend format.

        Pure function - no side effects, fully unit-testable

        Args:
            server_model: Raw model from Ollama API (must have "name" key)
            default_model: Default model name for is_default flag

        Returns:
            Frontend model dict with name, context_window, is_default
            None if server_model has no valid "name"

        Example:
            server_model = {"name": "llama3.2:3b", "size": 123456}
            default_model = "llama3.2:3b"
            Result: {
                "name": "llama3.2:3b",
                "context_window": 131072,
                "is_default": True
            }
        """
        model_name = server_model.get("name", "")

        if not model_name or not model_name.strip():
            return None

        return {
            "name": model_name,
            "context_window": get_context_window_size(model_name),
            "is_default": model_name == default_model,
        }

    @staticmethod
    def transform_server_models_to_frontend(
        server_models: list[dict[str, Any]], default_model: str
    ) -> list[dict[str, Any]]:
        """
        Transform list of Ollama server models to frontend format.

        Pure function - no side effects, fully unit-testable

        Args:
            server_models: List of raw models from Ollama API
            default_model: Default model name for is_default flag

        Returns:
            List of frontend model dicts (skips models without valid names)

        Example:
            server_models = [
                {"name": "llama3.2:3b", "size": 123},
                {"name": "", "size": 456},      # Skipped (no name)
                {"name": "qwen2.5:7b", "size": 789}
            ]
            Result: [
                {"name": "llama3.2:3b", "context_window": 131072, "is_default": True},
                {"name": "qwen2.5:7b", "context_window": 32768, "is_default": False}
            ]
        """
        frontend_models = []

        for server_model in server_models:
            frontend_model = OllamaModelTransformer.transform_server_model_to_frontend(server_model, default_model)
            if frontend_model:
                frontend_models.append(frontend_model)

        return frontend_models

    @staticmethod
    def build_static_model_list(configured_models: list[str], default_model: str) -> list[dict[str, Any]]:
        """
        Build static model list from configured model names.

        Pure function - no side effects, fully unit-testable

        Args:
            configured_models: List of model names from configuration
            default_model: Default model name for is_default flag

        Returns:
            List of frontend model dicts with name, context_window, is_default

        Example:
            configured_models = ["llama3.2:3b", "qwen2.5:7b"]
            default_model = "llama3.2:3b"
            Result: [
                {"name": "llama3.2:3b", "context_window": 131072, "is_default": True},
                {"name": "qwen2.5:7b", "context_window": 32768, "is_default": False}
            ]
        """
        models = []

        for model_name in configured_models:
            models.append(
                {
                    "name": model_name,
                    "context_window": get_context_window_size(model_name),
                    "is_default": model_name == default_model,
                }
            )

        return models
