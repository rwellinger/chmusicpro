"""Tests for Claude Chat Transformer - Business logic unit tests"""

import pytest

from business.claude_chat_transformer import (
    build_messages_payload,
    filter_models_by_whitelist,
    get_available_models,
    get_model_context_window,
    get_model_context_window_from_id,
    parse_configured_claude_models,
    parse_messages_response,
    transform_api_model_to_frontend,
    transform_api_models_to_frontend,
)


@pytest.mark.unit
class TestBuildMessagesPayload:
    """Test build_messages_payload() - Constructs Claude Messages API request"""

    def test_basic_payload_construction(self):
        """Should create valid payload with model, messages, max_tokens"""
        # Arrange
        model = "claude-3-opus-20240229"
        messages = [{"role": "user", "content": "Hello"}]
        max_tokens = 1000

        # Act
        payload = build_messages_payload(model, messages, max_tokens)

        # Assert
        assert payload["model"] == model
        assert payload["max_tokens"] == max_tokens
        assert payload["messages"] == messages
        assert payload["temperature"] == 0.7  # Default

    def test_system_message_extraction(self):
        """Should extract system messages into separate 'system' field"""
        # Arrange
        model = "claude-3-opus-20240229"
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        max_tokens = 1000

        # Act
        payload = build_messages_payload(model, messages, max_tokens)

        # Assert
        assert payload["system"] == "You are a helpful assistant"
        assert len(payload["messages"]) == 2  # Only user/assistant
        assert payload["messages"][0]["role"] == "user"
        assert payload["messages"][1]["role"] == "assistant"

    def test_multiple_system_messages(self):
        """Should extract multiple system messages (only last one used)"""
        # Arrange
        model = "claude-3-opus-20240229"
        messages = [
            {"role": "system", "content": "First system message"},
            {"role": "system", "content": "Second system message"},
            {"role": "user", "content": "Hello"},
        ]
        max_tokens = 1000

        # Act
        payload = build_messages_payload(model, messages, max_tokens)

        # Assert
        # Note: Current implementation only keeps last system message
        assert payload["system"] == "Second system message"
        assert len(payload["messages"]) == 1

    def test_temperature_clamped_to_max(self):
        """Temperature > 1.0 should be clamped to 1.0"""
        # Arrange
        model = "claude-3-opus-20240229"
        messages = [{"role": "user", "content": "Hello"}]
        max_tokens = 1000

        # Act
        payload = build_messages_payload(model, messages, max_tokens, temperature=1.5)

        # Assert
        assert payload["temperature"] == 1.0

    def test_temperature_clamped_to_min(self):
        """Temperature < 0.0 should be clamped to 0.0"""
        # Arrange
        model = "claude-3-opus-20240229"
        messages = [{"role": "user", "content": "Hello"}]
        max_tokens = 1000

        # Act
        payload = build_messages_payload(model, messages, max_tokens, temperature=-0.5)

        # Assert
        assert payload["temperature"] == 0.0

    def test_temperature_in_valid_range(self):
        """Temperature within 0.0-1.0 should remain unchanged"""
        # Arrange
        model = "claude-3-opus-20240229"
        messages = [{"role": "user", "content": "Hello"}]
        max_tokens = 1000

        # Act
        payload = build_messages_payload(model, messages, max_tokens, temperature=0.3)

        # Assert
        assert payload["temperature"] == 0.3

    def test_default_temperature(self):
        """Should use default temperature 0.7 when not specified"""
        # Arrange
        model = "claude-3-opus-20240229"
        messages = [{"role": "user", "content": "Hello"}]
        max_tokens = 1000

        # Act
        payload = build_messages_payload(model, messages, max_tokens)

        # Assert
        assert payload["temperature"] == 0.7

    def test_no_system_message(self):
        """Should not include 'system' field when no system messages"""
        # Arrange
        model = "claude-3-opus-20240229"
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]
        max_tokens = 1000

        # Act
        payload = build_messages_payload(model, messages, max_tokens)

        # Assert
        assert "system" not in payload
        assert len(payload["messages"]) == 2


@pytest.mark.unit
class TestParseMessagesResponse:
    """Test parse_messages_response() - Parses Claude Messages API response"""

    def test_valid_response_parsing(self):
        """Should parse valid Claude API response"""
        # Arrange
        response = {
            "content": [{"type": "text", "text": "Hello!"}],
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }

        # Act
        content, input_tokens, output_tokens = parse_messages_response(response)

        # Assert
        assert content == "Hello!"
        assert input_tokens == 10
        assert output_tokens == 5

    def test_multiple_text_blocks(self):
        """Should concatenate multiple text blocks"""
        # Arrange
        response = {
            "content": [
                {"type": "text", "text": "Part 1"},
                {"type": "text", "text": " Part 2"},
                {"type": "text", "text": " Part 3"},
            ],
            "usage": {"input_tokens": 10, "output_tokens": 15},
        }

        # Act
        content, input_tokens, output_tokens = parse_messages_response(response)

        # Assert
        assert content == "Part 1 Part 2 Part 3"
        assert input_tokens == 10
        assert output_tokens == 15

    def test_missing_usage_defaults_to_zero(self):
        """Should default to 0 tokens when usage field is missing"""
        # Arrange
        response = {"content": [{"type": "text", "text": "Hi"}]}

        # Act
        content, input_tokens, output_tokens = parse_messages_response(response)

        # Assert
        assert content == "Hi"
        assert input_tokens == 0
        assert output_tokens == 0

    def test_partial_usage_defaults(self):
        """Should default missing token counts to 0"""
        # Arrange
        response = {
            "content": [{"type": "text", "text": "Hello"}],
            "usage": {"input_tokens": 10},  # Missing output_tokens
        }

        # Act
        content, input_tokens, output_tokens = parse_messages_response(response)

        # Assert
        assert content == "Hello"
        assert input_tokens == 10
        assert output_tokens == 0

    def test_missing_content_raises_error(self):
        """Should raise ValueError when content field is missing"""
        # Arrange
        response = {"usage": {"input_tokens": 10, "output_tokens": 5}}

        # Act & Assert
        with pytest.raises(ValueError, match="no content found"):
            parse_messages_response(response)

    def test_empty_content_array_raises_error(self):
        """Should raise ValueError when content array is empty"""
        # Arrange
        response = {
            "content": [],
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }

        # Act & Assert
        with pytest.raises(ValueError, match="no content found"):
            parse_messages_response(response)

    def test_non_text_blocks_skipped(self):
        """Should skip non-text content blocks"""
        # Arrange
        response = {
            "content": [
                {"type": "text", "text": "Hello"},
                {"type": "image", "url": "https://example.com/image.jpg"},
                {"type": "text", "text": " World"},
            ],
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }

        # Act
        content, input_tokens, output_tokens = parse_messages_response(response)

        # Assert
        assert content == "Hello World"

    def test_empty_text_in_block(self):
        """Should handle empty text in content blocks"""
        # Arrange
        response = {
            "content": [
                {"type": "text", "text": ""},
                {"type": "text", "text": "Hello"},
            ],
            "usage": {"input_tokens": 5, "output_tokens": 2},
        }

        # Act
        content, input_tokens, output_tokens = parse_messages_response(response)

        # Assert
        assert content == "Hello"


@pytest.mark.unit
class TestGetModelContextWindow:
    """Test get_model_context_window() - Returns context window size"""

    def test_claude_3_opus(self):
        """Should return 200000 for Claude 3 Opus"""
        assert get_model_context_window("claude-3-opus-20240229") == 200000

    def test_claude_3_sonnet(self):
        """Should return 200000 for Claude 3 Sonnet"""
        assert get_model_context_window("claude-3-sonnet-20240229") == 200000

    def test_claude_3_haiku(self):
        """Should return 200000 for Claude 3 Haiku"""
        assert get_model_context_window("claude-3-haiku-20240307") == 200000

    def test_claude_sonnet_4_5(self):
        """Should return 200000 for Claude Sonnet 4.5"""
        assert get_model_context_window("claude-sonnet-4-5-20250929") == 200000

    def test_claude_haiku_4_5(self):
        """Should return 200000 for Claude Haiku 4.5"""
        assert get_model_context_window("claude-haiku-4-5-20250929") == 200000

    def test_claude_opus_4_5(self):
        """Should return 200000 for Claude Opus 4.5"""
        assert get_model_context_window("claude-opus-4-5-20251101") == 200000

    def test_unknown_model(self):
        """Should return 200000 for unknown models (default)"""
        assert get_model_context_window("claude-unknown-new-model") == 200000

    def test_future_model(self):
        """Should return 200000 for future models"""
        assert get_model_context_window("claude-6-ultra-20260101") == 200000


@pytest.mark.unit
class TestGetAvailableModels:
    """Test get_available_models() - Parses model configuration"""

    def test_single_model(self):
        """Should parse single model"""
        models_config = "claude-3-opus-20240229"

        models = get_available_models(models_config)

        assert len(models) == 1
        assert models[0]["name"] == "claude-3-opus-20240229"
        assert models[0]["context_window"] == 200000

    def test_multiple_models(self):
        """Should parse multiple comma-separated models"""
        models_config = "claude-3-opus-20240229,claude-3-sonnet-20240229"

        models = get_available_models(models_config)

        assert len(models) == 2
        assert models[0]["name"] == "claude-3-opus-20240229"
        assert models[0]["context_window"] == 200000
        assert models[1]["name"] == "claude-3-sonnet-20240229"
        assert models[1]["context_window"] == 200000

    def test_models_with_spaces(self):
        """Should handle spaces around commas"""
        models_config = "claude-3-opus-20240229 , claude-3-sonnet-20240229  ,  claude-3-haiku-20240307"

        models = get_available_models(models_config)

        assert len(models) == 3
        assert models[0]["name"] == "claude-3-opus-20240229"
        assert models[1]["name"] == "claude-3-sonnet-20240229"
        assert models[2]["name"] == "claude-3-haiku-20240307"

    def test_empty_string(self):
        """Should return empty list for empty string"""
        models_config = ""

        models = get_available_models(models_config)

        assert len(models) == 0

    def test_empty_entries_skipped(self):
        """Should skip empty entries after split"""
        models_config = "claude-3-opus-20240229,,claude-3-sonnet-20240229"

        models = get_available_models(models_config)

        assert len(models) == 2
        assert models[0]["name"] == "claude-3-opus-20240229"
        assert models[1]["name"] == "claude-3-sonnet-20240229"


@pytest.mark.unit
class TestGetModelContextWindowFromId:
    """Test get_model_context_window_from_id() - Maps model ID to context window"""

    def test_claude_2_1(self):
        """Should return 100000 for Claude 2.1"""
        assert get_model_context_window_from_id("claude-2.1") == 100000

    def test_claude_2_0(self):
        """Should return 100000 for Claude 2.0"""
        assert get_model_context_window_from_id("claude-2.0") == 100000

    def test_claude_instant(self):
        """Should return 100000 for Claude Instant"""
        assert get_model_context_window_from_id("claude-instant-1.2") == 100000

    def test_claude_3_opus(self):
        """Should return 200000 for Claude 3 Opus"""
        assert get_model_context_window_from_id("claude-3-opus-20240229") == 200000

    def test_claude_3_sonnet(self):
        """Should return 200000 for Claude 3 Sonnet"""
        assert get_model_context_window_from_id("claude-3-sonnet-20240229") == 200000

    def test_claude_3_5_sonnet(self):
        """Should return 200000 for Claude 3.5 Sonnet"""
        assert get_model_context_window_from_id("claude-3-5-sonnet-20241022") == 200000

    def test_claude_sonnet_4_5(self):
        """Should return 200000 for Claude Sonnet 4.5"""
        assert get_model_context_window_from_id("claude-sonnet-4-5-20250929") == 200000

    def test_claude_haiku_4_5(self):
        """Should return 200000 for Claude Haiku 4.5"""
        assert get_model_context_window_from_id("claude-haiku-4-5-20250929") == 200000

    def test_claude_opus_4_5(self):
        """Should return 200000 for Claude Opus 4.5"""
        assert get_model_context_window_from_id("claude-opus-4-5-20251101") == 200000

    def test_unknown_future_model(self):
        """Should return 200000 for unknown/future models (default)"""
        assert get_model_context_window_from_id("claude-future-model") == 200000

    def test_case_insensitive_claude_2(self):
        """Should handle case-insensitive matching for Claude-2"""
        assert get_model_context_window_from_id("Claude-2.1") == 100000
        assert get_model_context_window_from_id("CLAUDE-INSTANT-1.2") == 100000


@pytest.mark.unit
class TestParseConfiguredClaudeModels:
    """Test parse_configured_claude_models() - Parses model configuration"""

    def test_parse_with_whitespace(self):
        """Should trim whitespace around model names"""
        models_config = "  model1  ,  model2  "

        models = parse_configured_claude_models(models_config)

        assert models == ["model1", "model2"]

    def test_duplicate_removal_preserves_order(self):
        """Should remove duplicates while preserving order"""
        models_config = "model1,model2,model1,model3"

        models = parse_configured_claude_models(models_config)

        assert models == ["model1", "model2", "model3"]

    def test_empty_string(self):
        """Should return empty list for empty string"""
        models_config = ""

        models = parse_configured_claude_models(models_config)

        assert models == []

    def test_whitespace_only_string(self):
        """Should return empty list for whitespace-only string"""
        models_config = "   "

        models = parse_configured_claude_models(models_config)

        assert models == []

    def test_empty_entries_skipped(self):
        """Should skip empty entries after split"""
        models_config = "model1,,model2,  ,model3"

        models = parse_configured_claude_models(models_config)

        assert models == ["model1", "model2", "model3"]

    def test_real_claude_models(self):
        """Should parse real Claude model names"""
        models_config = "claude-3-opus-20240229, claude-3-sonnet-20240229, claude-3-haiku-20240307"

        models = parse_configured_claude_models(models_config)

        assert models == [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]


@pytest.mark.unit
class TestTransformApiModelToFrontend:
    """Test transform_api_model_to_frontend() - Transforms API model to frontend format"""

    def test_valid_model(self):
        """Should transform valid model"""
        api_model = {"id": "claude-3-opus-20240229", "type": "model"}

        result = transform_api_model_to_frontend(api_model)

        assert result == {"name": "claude-3-opus-20240229", "context_window": 200000}

    def test_filter_embeddings(self):
        """Should return None for embedding models"""
        api_model = {"id": "claude-embedding-v1", "type": "embedding"}

        result = transform_api_model_to_frontend(api_model)

        assert result is None

    def test_missing_id_field(self):
        """Should return None when ID field is missing"""
        api_model = {"type": "model"}

        result = transform_api_model_to_frontend(api_model)

        assert result is None

    def test_empty_id_string(self):
        """Should return None when ID is empty string"""
        api_model = {"id": "", "type": "model"}

        result = transform_api_model_to_frontend(api_model)

        assert result is None

    def test_whitespace_only_id(self):
        """Should return None when ID is whitespace only"""
        api_model = {"id": "   ", "type": "model"}

        result = transform_api_model_to_frontend(api_model)

        assert result is None

    def test_missing_type_field(self):
        """Should return None when type field is missing"""
        api_model = {"id": "claude-3-opus-20240229"}

        result = transform_api_model_to_frontend(api_model)

        assert result is None

    def test_wrong_type(self):
        """Should return None for non-model types"""
        api_model = {"id": "claude-3-opus-20240229", "type": "fine-tuned"}

        result = transform_api_model_to_frontend(api_model)

        assert result is None

    def test_claude_2_model(self):
        """Should map Claude 2 model to 100k context window"""
        api_model = {"id": "claude-2.1", "type": "model"}

        result = transform_api_model_to_frontend(api_model)

        assert result == {"name": "claude-2.1", "context_window": 100000}


@pytest.mark.unit
class TestTransformApiModelsToFrontend:
    """Test transform_api_models_to_frontend() - Batch transforms API models"""

    def test_batch_transformation(self):
        """Should transform multiple models and skip invalid ones"""
        api_models = [
            {"id": "claude-3-opus-20240229", "type": "model"},
            {"id": "", "type": "model"},  # Skipped (no ID)
            {"id": "claude-3-sonnet-20240229", "type": "model"},
            {"id": "claude-embedding-v1", "type": "embedding"},  # Skipped (not chat model)
        ]

        result = transform_api_models_to_frontend(api_models)

        assert len(result) == 2
        assert result[0]["name"] == "claude-3-opus-20240229"
        assert result[0]["context_window"] == 200000
        assert result[1]["name"] == "claude-3-sonnet-20240229"
        assert result[1]["context_window"] == 200000

    def test_empty_list(self):
        """Should return empty list for empty input"""
        api_models = []

        result = transform_api_models_to_frontend(api_models)

        assert result == []

    def test_all_invalid_models(self):
        """Should return empty list when all models are invalid"""
        api_models = [
            {"id": "", "type": "model"},
            {"id": "embedding-1", "type": "embedding"},
            {"type": "model"},  # Missing ID
        ]

        result = transform_api_models_to_frontend(api_models)

        assert result == []

    def test_mixed_context_windows(self):
        """Should correctly map different context windows"""
        api_models = [
            {"id": "claude-2.1", "type": "model"},  # 100k
            {"id": "claude-3-opus-20240229", "type": "model"},  # 200k
            {"id": "claude-instant-1.2", "type": "model"},  # 100k
        ]

        result = transform_api_models_to_frontend(api_models)

        assert len(result) == 3
        assert result[0]["context_window"] == 100000
        assert result[1]["context_window"] == 200000
        assert result[2]["context_window"] == 100000


@pytest.mark.unit
class TestFilterModelsByWhitelist:
    """Test filter_models_by_whitelist() - Filters models by whitelist"""

    def test_empty_whitelist_returns_all(self):
        """Should return all models when whitelist is empty"""
        models = [
            {"name": "claude-3-opus-20240229", "context_window": 200000},
            {"name": "claude-3-sonnet-20240229", "context_window": 200000},
            {"name": "claude-3-haiku-20240307", "context_window": 200000},
        ]
        whitelist = []

        result = filter_models_by_whitelist(models, whitelist)

        assert len(result) == 3
        assert result == models

    def test_partial_match(self):
        """Should return only whitelisted models"""
        models = [
            {"name": "claude-3-opus-20240229", "context_window": 200000},
            {"name": "claude-3-sonnet-20240229", "context_window": 200000},
            {"name": "claude-3-haiku-20240307", "context_window": 200000},
        ]
        whitelist = ["claude-3-opus-20240229", "claude-3-haiku-20240307"]

        result = filter_models_by_whitelist(models, whitelist)

        assert len(result) == 2
        assert result[0]["name"] == "claude-3-opus-20240229"
        assert result[1]["name"] == "claude-3-haiku-20240307"

    def test_no_matches(self):
        """Should return empty list when no models match"""
        models = [
            {"name": "claude-3-opus-20240229", "context_window": 200000},
            {"name": "claude-3-sonnet-20240229", "context_window": 200000},
        ]
        whitelist = ["nonexistent-model"]

        result = filter_models_by_whitelist(models, whitelist)

        assert result == []

    def test_single_match(self):
        """Should return single matching model"""
        models = [
            {"name": "claude-3-opus-20240229", "context_window": 200000},
            {"name": "claude-3-sonnet-20240229", "context_window": 200000},
            {"name": "claude-3-haiku-20240307", "context_window": 200000},
        ]
        whitelist = ["claude-3-sonnet-20240229"]

        result = filter_models_by_whitelist(models, whitelist)

        assert len(result) == 1
        assert result[0]["name"] == "claude-3-sonnet-20240229"

    def test_whitelist_order_does_not_affect_result(self):
        """Should preserve original model order, not whitelist order"""
        models = [
            {"name": "model1", "context_window": 200000},
            {"name": "model2", "context_window": 200000},
            {"name": "model3", "context_window": 200000},
        ]
        whitelist = ["model3", "model1"]  # Different order than models

        result = filter_models_by_whitelist(models, whitelist)

        assert len(result) == 2
        assert result[0]["name"] == "model1"  # Original order preserved
        assert result[1]["name"] == "model3"

    def test_empty_models_list(self):
        """Should return empty list when models list is empty"""
        models = []
        whitelist = ["claude-3-opus-20240229"]

        result = filter_models_by_whitelist(models, whitelist)

        assert result == []
