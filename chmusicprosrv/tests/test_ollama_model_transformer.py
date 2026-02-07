"""Tests for OllamaModelTransformer - Business logic unit tests"""

from business.ollama_model_transformer import OllamaModelTransformer


class TestParseConfiguredModels:
    """Test parse_configured_models() - model string parsing"""

    def test_parse_single_model(self):
        """Parse single model name"""
        result = OllamaModelTransformer.parse_configured_models("llama3.2:3b")
        assert result == ["llama3.2:3b"]

    def test_parse_multiple_models(self):
        """Parse multiple model names"""
        result = OllamaModelTransformer.parse_configured_models("llama3.2:3b,qwen2.5:7b,mistral:7b")
        assert result == ["llama3.2:3b", "qwen2.5:7b", "mistral:7b"]

    def test_parse_with_spaces(self):
        """Parse models with spaces around commas"""
        result = OllamaModelTransformer.parse_configured_models("llama3.2:3b , qwen2.5:7b , mistral:7b")
        assert result == ["llama3.2:3b", "qwen2.5:7b", "mistral:7b"]

    def test_parse_with_leading_trailing_spaces(self):
        """Parse models with leading/trailing spaces"""
        result = OllamaModelTransformer.parse_configured_models("  llama3.2:3b  ,  qwen2.5:7b  ")
        assert result == ["llama3.2:3b", "qwen2.5:7b"]

    def test_parse_empty_string(self):
        """Empty string returns empty list"""
        result = OllamaModelTransformer.parse_configured_models("")
        assert result == []

    def test_parse_whitespace_only(self):
        """Whitespace-only string returns empty list"""
        result = OllamaModelTransformer.parse_configured_models("   ")
        assert result == []

    def test_parse_with_empty_entries(self):
        """Parse with empty entries between commas"""
        result = OllamaModelTransformer.parse_configured_models("llama3.2:3b,,qwen2.5:7b")
        assert result == ["llama3.2:3b", "qwen2.5:7b"]

    def test_parse_trailing_comma(self):
        """Parse with trailing comma"""
        result = OllamaModelTransformer.parse_configured_models("llama3.2:3b,qwen2.5:7b,")
        assert result == ["llama3.2:3b", "qwen2.5:7b"]

    def test_parse_leading_comma(self):
        """Parse with leading comma"""
        result = OllamaModelTransformer.parse_configured_models(",llama3.2:3b,qwen2.5:7b")
        assert result == ["llama3.2:3b", "qwen2.5:7b"]

    def test_parse_duplicates_removed(self):
        """Duplicates are removed (first occurrence kept)"""
        result = OllamaModelTransformer.parse_configured_models("llama3.2:3b,qwen2.5:7b,llama3.2:3b")
        assert result == ["llama3.2:3b", "qwen2.5:7b"]

    def test_parse_preserves_order(self):
        """Order is preserved"""
        result = OllamaModelTransformer.parse_configured_models("model3,model1,model2")
        assert result == ["model3", "model1", "model2"]


class TestTransformServerModelToFrontend:
    """Test transform_server_model_to_frontend() - single model transformation"""

    def test_transform_valid_model_is_default(self):
        """Transform valid model (is default)"""
        server_model = {"name": "llama3.2:3b", "size": 123456}
        default_model = "llama3.2:3b"

        result = OllamaModelTransformer.transform_server_model_to_frontend(server_model, default_model)

        assert result is not None
        assert result["name"] == "llama3.2:3b"
        assert result["context_window"] == 131072  # From model_context_windows.py
        assert result["is_default"] is True

    def test_transform_valid_model_not_default(self):
        """Transform valid model (not default)"""
        server_model = {"name": "qwen2:7b", "size": 123456}
        default_model = "llama3.2:3b"

        result = OllamaModelTransformer.transform_server_model_to_frontend(server_model, default_model)

        assert result is not None
        assert result["name"] == "qwen2:7b"
        assert result["context_window"] == 32768  # From model_context_windows.py
        assert result["is_default"] is False

    def test_transform_model_without_name(self):
        """Model without name returns None"""
        server_model = {"size": 123456}
        default_model = "llama3.2:3b"

        result = OllamaModelTransformer.transform_server_model_to_frontend(server_model, default_model)

        assert result is None

    def test_transform_model_empty_name(self):
        """Model with empty name returns None"""
        server_model = {"name": "", "size": 123456}
        default_model = "llama3.2:3b"

        result = OllamaModelTransformer.transform_server_model_to_frontend(server_model, default_model)

        assert result is None

    def test_transform_model_whitespace_name(self):
        """Model with whitespace-only name returns None"""
        server_model = {"name": "   ", "size": 123456}
        default_model = "llama3.2:3b"

        result = OllamaModelTransformer.transform_server_model_to_frontend(server_model, default_model)

        assert result is None

    def test_transform_unknown_model_uses_default_context(self):
        """Unknown model uses default context window (2048)"""
        server_model = {"name": "unknown-model:1b", "size": 123456}
        default_model = "llama3.2:3b"

        result = OllamaModelTransformer.transform_server_model_to_frontend(server_model, default_model)

        assert result is not None
        assert result["name"] == "unknown-model:1b"
        assert result["context_window"] == 2048  # Default from model_context_windows.py
        assert result["is_default"] is False


class TestTransformServerModelsToFrontend:
    """Test transform_server_models_to_frontend() - batch transformation"""

    def test_transform_multiple_models(self):
        """Transform multiple valid models"""
        server_models = [
            {"name": "llama3.2:3b", "size": 123},
            {"name": "qwen2:7b", "size": 456},
            {"name": "mistral:7b", "size": 789},
        ]
        default_model = "llama3.2:3b"

        result = OllamaModelTransformer.transform_server_models_to_frontend(server_models, default_model)

        assert len(result) == 3
        assert result[0]["name"] == "llama3.2:3b"
        assert result[0]["is_default"] is True
        assert result[1]["name"] == "qwen2:7b"
        assert result[1]["is_default"] is False
        assert result[2]["name"] == "mistral:7b"
        assert result[2]["is_default"] is False

    def test_transform_empty_list(self):
        """Empty server model list returns empty list"""
        result = OllamaModelTransformer.transform_server_models_to_frontend([], "llama3.2:3b")
        assert result == []

    def test_transform_with_invalid_models(self):
        """Invalid models are skipped"""
        server_models = [
            {"name": "llama3.2:3b", "size": 123},
            {"name": "", "size": 456},  # Skipped (empty name)
            {"size": 789},  # Skipped (no name)
            {"name": "qwen2:7b", "size": 101112},
        ]
        default_model = "llama3.2:3b"

        result = OllamaModelTransformer.transform_server_models_to_frontend(server_models, default_model)

        assert len(result) == 2
        assert result[0]["name"] == "llama3.2:3b"
        assert result[1]["name"] == "qwen2:7b"

    def test_transform_all_invalid_models(self):
        """All invalid models returns empty list"""
        server_models = [{"name": "", "size": 123}, {"size": 456}, {"name": "   ", "size": 789}]
        default_model = "llama3.2:3b"

        result = OllamaModelTransformer.transform_server_models_to_frontend(server_models, default_model)

        assert result == []


class TestBuildStaticModelList:
    """Test build_static_model_list() - static model list building"""

    def test_build_single_model(self):
        """Build list with single model"""
        configured_models = ["llama3.2:3b"]
        default_model = "llama3.2:3b"

        result = OllamaModelTransformer.build_static_model_list(configured_models, default_model)

        assert len(result) == 1
        assert result[0]["name"] == "llama3.2:3b"
        assert result[0]["context_window"] == 131072
        assert result[0]["is_default"] is True

    def test_build_multiple_models(self):
        """Build list with multiple models"""
        configured_models = ["llama3.2:3b", "qwen2:7b", "mistral:7b"]
        default_model = "llama3.2:3b"

        result = OllamaModelTransformer.build_static_model_list(configured_models, default_model)

        assert len(result) == 3
        assert result[0]["name"] == "llama3.2:3b"
        assert result[0]["is_default"] is True
        assert result[1]["name"] == "qwen2:7b"
        assert result[1]["is_default"] is False
        assert result[2]["name"] == "mistral:7b"
        assert result[2]["is_default"] is False

    def test_build_empty_list(self):
        """Empty configured models returns empty list"""
        result = OllamaModelTransformer.build_static_model_list([], "llama3.2:3b")
        assert result == []

    def test_build_no_default_match(self):
        """No model matches default - all is_default=False"""
        configured_models = ["qwen2:7b", "mistral:7b"]
        default_model = "llama3.2:3b"

        result = OllamaModelTransformer.build_static_model_list(configured_models, default_model)

        assert len(result) == 2
        assert result[0]["is_default"] is False
        assert result[1]["is_default"] is False

    def test_build_preserves_order(self):
        """Build preserves model order"""
        configured_models = ["model3", "model1", "model2"]
        default_model = "model1"

        result = OllamaModelTransformer.build_static_model_list(configured_models, default_model)

        assert len(result) == 3
        assert result[0]["name"] == "model3"
        assert result[1]["name"] == "model1"
        assert result[2]["name"] == "model2"
