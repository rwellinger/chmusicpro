"""Unit tests for Pydantic schema validators (V2 migration)."""

import pytest
from pydantic import ValidationError

from src.schemas.chat_schemas import ChatRequest, UnifiedChatRequest
from src.schemas.image_schemas import ImageGenerateRequest, ImageListRequest
from src.schemas.prompt_schemas import PromptTemplateBase, PromptTemplateUpdate
from src.schemas.user_schemas import PasswordChangeRequest, PasswordResetRequest, UserCreateRequest


# ========================================
# Chat Schemas Tests (2 validators)
# ========================================


class TestChatRequest:
    """Test ChatRequest validators."""

    def test_valid_model(self):
        """Valid model should pass validation."""
        data = {"model": "llama3.2:3b", "prompt": "test prompt"}
        request = ChatRequest(**data)
        assert request.model == "llama3.2:3b"

    def test_any_model_accepted(self):
        """Any model name should pass (validation moved to adapter layer)."""
        data = {"model": "gpt-5-turbo", "prompt": "test prompt"}
        request = ChatRequest(**data)
        assert request.model == "gpt-5-turbo"


class TestUnifiedChatRequest:
    """Test UnifiedChatRequest validators."""

    def test_valid_model(self):
        """Valid model should pass validation."""
        data = {"input_text": "test", "model": "deepseek-r1:8b"}
        request = UnifiedChatRequest(**data)
        assert request.model == "deepseek-r1:8b"

    def test_any_model_accepted(self):
        """Any model name should pass (validation moved to adapter layer)."""
        data = {"input_text": "test", "model": "claude-haiku-4-5-20250929"}
        request = UnifiedChatRequest(**data)
        assert request.model == "claude-haiku-4-5-20250929"

    def test_none_model(self):
        """None model should pass (optional field)."""
        data = {"input_text": "test", "model": None}
        request = UnifiedChatRequest(**data)
        assert request.model is None


# ========================================
# Image Schemas Tests (3 validators)
# ========================================


class TestImageGenerateRequest:
    """Test ImageGenerateRequest validators."""

    def test_valid_size(self):
        """Valid size should pass validation."""
        data = {"prompt": "test", "size": "1024x1024"}
        request = ImageGenerateRequest(**data)
        assert request.size == "1024x1024"

    def test_invalid_size(self):
        """Invalid size should raise ValidationError."""
        data = {"prompt": "test", "size": "2048x2048"}
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerateRequest(**data)
        assert "size must be one of" in str(exc_info.value)


class TestImageListRequest:
    """Test ImageListRequest validators."""

    def test_valid_sort(self):
        """Valid sort field should pass validation."""
        data = {"sort": "created_at"}
        request = ImageListRequest(**data)
        assert request.sort == "created_at"

    def test_invalid_sort(self):
        """Invalid sort field should raise ValidationError."""
        data = {"sort": "invalid_field"}
        with pytest.raises(ValidationError) as exc_info:
            ImageListRequest(**data)
        assert "sort must be one of" in str(exc_info.value)

    def test_valid_order(self):
        """Valid order should pass validation."""
        data = {"order": "asc"}
        request = ImageListRequest(**data)
        assert request.order == "asc"

    def test_invalid_order(self):
        """Invalid order should raise ValidationError."""
        data = {"order": "invalid"}
        with pytest.raises(ValidationError) as exc_info:
            ImageListRequest(**data)
        assert "order must be either asc or desc" in str(exc_info.value)


# ========================================
# User Schemas Tests (3 validators)
# ========================================


class TestUserCreateRequest:
    """Test UserCreateRequest validators."""

    def test_valid_password(self):
        """Valid password (>= 4 chars) should pass validation."""
        data = {"email": "test@example.com", "password": "test1234"}
        request = UserCreateRequest(**data)
        assert request.password == "test1234"

    def test_short_password(self):
        """Password < 4 chars should raise ValidationError."""
        data = {"email": "test@example.com", "password": "abc"}
        with pytest.raises(ValidationError) as exc_info:
            UserCreateRequest(**data)
        assert "at least 4 characters" in str(exc_info.value)


class TestPasswordChangeRequest:
    """Test PasswordChangeRequest validators."""

    def test_valid_new_password(self):
        """Valid new password should pass validation."""
        data = {"old_password": "oldpass", "new_password": "newpass123"}
        request = PasswordChangeRequest(**data)
        assert request.new_password == "newpass123"

    def test_short_new_password(self):
        """Short new password should raise ValidationError."""
        data = {"old_password": "oldpass", "new_password": "abc"}
        with pytest.raises(ValidationError) as exc_info:
            PasswordChangeRequest(**data)
        assert "at least 4 characters" in str(exc_info.value)


class TestPasswordResetRequest:
    """Test PasswordResetRequest validators."""

    def test_valid_new_password(self):
        """Valid new password should pass validation."""
        data = {"email": "test@example.com", "new_password": "newpass123"}
        request = PasswordResetRequest(**data)
        assert request.new_password == "newpass123"

    def test_short_new_password(self):
        """Short new password should raise ValidationError."""
        data = {"email": "test@example.com", "new_password": "abc"}
        with pytest.raises(ValidationError) as exc_info:
            PasswordResetRequest(**data)
        assert "at least 4 characters" in str(exc_info.value)


# ========================================
# Prompt Schemas Tests (2 validators)
# ========================================


class TestPromptTemplateBase:
    """Test PromptTemplateBase validators."""

    def test_valid_model(self):
        """Valid model should pass validation."""
        data = {
            "category": "test",
            "action": "test",
            "pre_condition": "test",
            "post_condition": "test",
            "model": "gemma3:4b",
        }
        template = PromptTemplateBase(**data)
        assert template.model == "gemma3:4b"

    def test_any_model_accepted(self):
        """Any model name should pass (validation moved to adapter layer)."""
        data = {
            "category": "test",
            "action": "test",
            "pre_condition": "test",
            "post_condition": "test",
            "model": "gpt-4.1-mini",
        }
        template = PromptTemplateBase(**data)
        assert template.model == "gpt-4.1-mini"

    def test_none_model(self):
        """None model should pass (optional field)."""
        data = {"category": "test", "action": "test", "pre_condition": "test", "post_condition": "test", "model": None}
        template = PromptTemplateBase(**data)
        assert template.model is None

    def test_provider_defaults_to_ollama(self):
        """Provider should default to 'ollama' when not specified."""
        data = {"category": "test", "action": "test", "pre_condition": "test", "post_condition": "test"}
        template = PromptTemplateBase(**data)
        assert template.provider == "ollama"

    def test_provider_can_be_set(self):
        """Provider should accept any valid provider name."""
        data = {
            "category": "test",
            "action": "test",
            "pre_condition": "test",
            "post_condition": "test",
            "provider": "openai",
        }
        template = PromptTemplateBase(**data)
        assert template.provider == "openai"


class TestPromptTemplateUpdate:
    """Test PromptTemplateUpdate validators."""

    def test_valid_model(self):
        """Valid model should pass validation."""
        data = {"model": "llama3.2:3b"}
        update = PromptTemplateUpdate(**data)
        assert update.model == "llama3.2:3b"

    def test_any_model_accepted(self):
        """Any model name should pass (validation moved to adapter layer)."""
        data = {"model": "claude-sonnet-4-5-20250929"}
        update = PromptTemplateUpdate(**data)
        assert update.model == "claude-sonnet-4-5-20250929"

    def test_none_model(self):
        """None model should pass (optional field)."""
        data = {"model": None}
        update = PromptTemplateUpdate(**data)
        assert update.model is None
