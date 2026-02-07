"""Tests for OpenAI Chat Transformer - Business logic unit tests"""

import pytest

from business.openai_chat_transformer import (
    build_chat_payload,
    get_available_models,
    get_model_context_window,
    parse_chat_response,
)


class TestBuildChatPayload:
    """Test build_chat_payload() - OpenAI API payload construction"""

    def test_basic_payload(self):
        """Build basic payload with model and messages"""
        model = "gpt-4o"
        messages = [{"role": "user", "content": "Hello"}]

        payload = build_chat_payload(model, messages)

        assert payload["model"] == "gpt-4o"
        assert payload["messages"] == messages
        assert payload["temperature"] == 0.7  # Default

    def test_custom_temperature(self):
        """Build payload with custom temperature"""
        model = "gpt-4o"
        messages = [{"role": "user", "content": "Hello"}]
        temperature = 0.5

        payload = build_chat_payload(model, messages, temperature=temperature)

        assert payload["temperature"] == 0.5

    def test_gpt5_no_temperature(self):
        """GPT-5 models should not include temperature parameter"""
        model = "gpt-5"
        messages = [{"role": "user", "content": "Hello"}]

        payload = build_chat_payload(model, messages, temperature=0.5)

        assert "temperature" not in payload
        assert payload["model"] == "gpt-5"

    def test_gpt5_pro_no_temperature(self):
        """GPT-5-pro should not include temperature parameter"""
        model = "gpt-5-pro"
        messages = [{"role": "user", "content": "Hello"}]

        payload = build_chat_payload(model, messages)

        assert "temperature" not in payload

    def test_max_tokens_included(self):
        """Build payload with max_tokens (uses max_completion_tokens in payload)"""
        model = "gpt-4o"
        messages = [{"role": "user", "content": "Hello"}]
        max_tokens = 100

        payload = build_chat_payload(model, messages, max_tokens=max_tokens)

        # OpenAI deprecated max_tokens in favor of max_completion_tokens
        assert payload["max_completion_tokens"] == 100
        assert "max_tokens" not in payload

    def test_max_tokens_none(self):
        """Build payload without max_tokens (None)"""
        model = "gpt-4o"
        messages = [{"role": "user", "content": "Hello"}]

        payload = build_chat_payload(model, messages, max_tokens=None)

        assert "max_completion_tokens" not in payload
        assert "max_tokens" not in payload

    def test_multiple_messages(self):
        """Build payload with multiple messages"""
        model = "gpt-4o"
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        payload = build_chat_payload(model, messages)

        assert len(payload["messages"]) == 3
        assert payload["messages"][0]["role"] == "system"


class TestParseChatResponse:
    """Test parse_chat_response() - OpenAI API response parsing"""

    def test_valid_response(self):
        """Parse valid OpenAI response"""
        response = {
            "choices": [{"message": {"content": "Hello!"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

        content, prompt_tokens, completion_tokens = parse_chat_response(response)

        assert content == "Hello!"
        assert prompt_tokens == 10
        assert completion_tokens == 5

    def test_empty_content(self):
        """Parse response with empty content"""
        response = {
            "choices": [{"message": {"content": ""}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 0},
        }

        content, prompt_tokens, completion_tokens = parse_chat_response(response)

        assert content == ""
        assert prompt_tokens == 5
        assert completion_tokens == 0

    def test_missing_usage(self):
        """Parse response without usage field (default to 0)"""
        response = {
            "choices": [{"message": {"content": "Hello!"}}],
        }

        content, prompt_tokens, completion_tokens = parse_chat_response(response)

        assert content == "Hello!"
        assert prompt_tokens == 0
        assert completion_tokens == 0

    def test_no_choices(self):
        """Parse response without choices raises ValueError"""
        response = {"usage": {"prompt_tokens": 10, "completion_tokens": 5}}

        with pytest.raises(ValueError, match="no choices found"):
            parse_chat_response(response)

    def test_empty_choices(self):
        """Parse response with empty choices array raises ValueError"""
        response = {"choices": [], "usage": {"prompt_tokens": 10, "completion_tokens": 5}}

        with pytest.raises(ValueError, match="no choices found"):
            parse_chat_response(response)

    def test_missing_message(self):
        """Parse response without message field (empty content)"""
        response = {
            "choices": [{}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

        content, prompt_tokens, completion_tokens = parse_chat_response(response)

        assert content == ""
        assert prompt_tokens == 10

    def test_partial_usage(self):
        """Parse response with partial usage data"""
        response = {
            "choices": [{"message": {"content": "Hello!"}}],
            "usage": {"prompt_tokens": 10},  # Missing completion_tokens
        }

        content, prompt_tokens, completion_tokens = parse_chat_response(response)

        assert content == "Hello!"
        assert prompt_tokens == 10
        assert completion_tokens == 0  # Default


class TestGetModelContextWindow:
    """Test get_model_context_window() - Context window lookup"""

    def test_gpt5_context_window(self):
        """Get context window for GPT-5 models"""
        from config.model_context_windows import MODEL_CONTEXT_WINDOWS

        expected = MODEL_CONTEXT_WINDOWS.get("gpt-5", 2048)
        assert get_model_context_window("gpt-5") == expected

        expected_pro = MODEL_CONTEXT_WINDOWS.get("gpt-5-pro", 2048)
        assert get_model_context_window("gpt-5-pro") == expected_pro

        expected_mini = MODEL_CONTEXT_WINDOWS.get("gpt-5-mini", 2048)
        assert get_model_context_window("gpt-5-mini") == expected_mini

    def test_gpt4o_context_window(self):
        """Get context window for GPT-4o models"""
        from config.model_context_windows import MODEL_CONTEXT_WINDOWS

        expected = MODEL_CONTEXT_WINDOWS.get("gpt-4o", 2048)
        assert get_model_context_window("gpt-4o") == expected

        expected_mini = MODEL_CONTEXT_WINDOWS.get("gpt-4o-mini", 2048)
        assert get_model_context_window("gpt-4o-mini") == expected_mini

    def test_gpt4_context_window(self):
        """Get context window for GPT-4 models"""
        from config.model_context_windows import MODEL_CONTEXT_WINDOWS

        expected_turbo = MODEL_CONTEXT_WINDOWS.get("gpt-4-turbo", 2048)
        assert get_model_context_window("gpt-4-turbo") == expected_turbo

        expected = MODEL_CONTEXT_WINDOWS.get("gpt-4", 2048)
        assert get_model_context_window("gpt-4") == expected

    def test_gpt35_context_window(self):
        """Get context window for GPT-3.5 models"""
        from config.model_context_windows import MODEL_CONTEXT_WINDOWS

        expected = MODEL_CONTEXT_WINDOWS.get("gpt-3.5-turbo", 2048)
        assert get_model_context_window("gpt-3.5-turbo") == expected

    def test_unknown_model(self):
        """Get context window for unknown model (default from central config)"""
        from config.model_context_windows import MODEL_CONTEXT_WINDOWS

        expected_default = MODEL_CONTEXT_WINDOWS.get("default", 2048)
        assert get_model_context_window("unknown-model") == expected_default
        assert get_model_context_window("gpt-6") == expected_default

    def test_new_models_auto_available(self):
        """Test that new models from central config are automatically available"""
        from config.model_context_windows import MODEL_CONTEXT_WINDOWS

        # Test new GPT-4.1 series (should be in central config but was missing in old hardcoded dict)
        if "gpt-4.1" in MODEL_CONTEXT_WINDOWS:
            expected = MODEL_CONTEXT_WINDOWS["gpt-4.1"]
            assert get_model_context_window("gpt-4.1") == expected

        # Test new GPT-5.1 series
        if "gpt-5.1" in MODEL_CONTEXT_WINDOWS:
            expected = MODEL_CONTEXT_WINDOWS["gpt-5.1"]
            assert get_model_context_window("gpt-5.1") == expected

    def test_pattern_fallback_gpt5_series(self):
        """Test pattern-based fallback for unknown GPT-5 models (gpt-5.2, gpt-5.3, etc.)"""
        # These models are NOT in central config but should get 200k via pattern matching
        assert get_model_context_window("gpt-5.2") == 200000
        assert get_model_context_window("gpt-5.3") == 200000
        assert get_model_context_window("gpt-5.2-mini") == 200000
        assert get_model_context_window("gpt-5-ultra") == 200000

    def test_pattern_fallback_gpt4o_series(self):
        """Test pattern-based fallback for unknown GPT-4o models"""
        assert get_model_context_window("gpt-4o-ultra") == 128000
        assert get_model_context_window("gpt-4o-2025-01") == 128000

    def test_pattern_fallback_gpt4_series(self):
        """Test pattern-based fallback for unknown GPT-4 models"""
        assert get_model_context_window("gpt-4-preview") == 8192
        assert get_model_context_window("gpt-4-new") == 8192

    def test_pattern_fallback_gpt35_series(self):
        """Test pattern-based fallback for unknown GPT-3.5 models"""
        assert get_model_context_window("gpt-3.5-turbo-new") == 16385
        assert get_model_context_window("gpt-3.5-preview") == 16385


class TestGetAvailableModels:
    """Test get_available_models() - Model list parsing"""

    def test_single_model(self):
        """Parse single model"""
        models_config = "gpt-4o"

        models = get_available_models(models_config)

        assert len(models) == 1
        assert models[0]["name"] == "gpt-4o"
        assert models[0]["context_window"] == 128000

    def test_multiple_models(self):
        """Parse multiple models"""
        models_config = "gpt-4o,gpt-3.5-turbo"

        models = get_available_models(models_config)

        assert len(models) == 2
        assert models[0]["name"] == "gpt-4o"
        assert models[0]["context_window"] == 128000
        assert models[1]["name"] == "gpt-3.5-turbo"
        assert models[1]["context_window"] == 16385

    def test_model_with_spaces(self):
        """Parse models with spaces around commas"""
        models_config = "gpt-4o , gpt-3.5-turbo ,gpt-5"

        models = get_available_models(models_config)

        assert len(models) == 3
        assert models[0]["name"] == "gpt-4o"
        assert models[1]["name"] == "gpt-3.5-turbo"
        assert models[2]["name"] == "gpt-5"
        assert models[2]["context_window"] == 200000

    def test_unknown_models(self):
        """Parse unknown models (default context window from central config)"""
        from config.model_context_windows import MODEL_CONTEXT_WINDOWS

        models_config = "unknown-model-1,unknown-model-2"

        models = get_available_models(models_config)

        expected_default = MODEL_CONTEXT_WINDOWS.get("default", 2048)
        assert len(models) == 2
        assert models[0]["name"] == "unknown-model-1"
        assert models[0]["context_window"] == expected_default
        assert models[1]["name"] == "unknown-model-2"
        assert models[1]["context_window"] == expected_default

    def test_empty_string(self):
        """Parse empty string (single empty model)"""
        models_config = ""

        models = get_available_models(models_config)

        assert len(models) == 1
        assert models[0]["name"] == ""
