"""Tests for PromptTemplateValidator - Business logic unit tests"""

import pytest

from business.prompt_template_validator import (
    PromptTemplateValidationError,
    PromptTemplateValidator,
)


class TestValidateCategoryActionFormat:
    """Test category and action validation"""

    def test_valid_category_and_action(self):
        """Valid category and action - no exception"""
        PromptTemplateValidator.validate_category_action_format("lyrics", "generate")
        # No assertion needed - should not raise

    def test_empty_category_raises(self):
        """Empty category raises exception"""
        with pytest.raises(PromptTemplateValidationError, match="Category is required"):
            PromptTemplateValidator.validate_category_action_format("", "generate")

    def test_empty_action_raises(self):
        """Empty action raises exception"""
        with pytest.raises(PromptTemplateValidationError, match="Action is required"):
            PromptTemplateValidator.validate_category_action_format("lyrics", "")

    def test_whitespace_category_raises(self):
        """Whitespace-only category raises exception"""
        with pytest.raises(PromptTemplateValidationError, match="Category is required"):
            PromptTemplateValidator.validate_category_action_format("   ", "generate")

    def test_whitespace_action_raises(self):
        """Whitespace-only action raises exception"""
        with pytest.raises(PromptTemplateValidationError, match="Action is required"):
            PromptTemplateValidator.validate_category_action_format("lyrics", "   ")

    def test_both_empty_raises(self):
        """Both empty raises exception (category first)"""
        with pytest.raises(PromptTemplateValidationError, match="Category is required"):
            PromptTemplateValidator.validate_category_action_format("", "")

    def test_various_valid_categories(self):
        """Various valid category/action combinations"""
        valid_pairs = [
            ("lyrics", "generate"),
            ("image", "enhance"),
            ("music", "translate"),
            ("title", "generate"),
            ("custom_category", "custom_action"),
        ]
        for category, action in valid_pairs:
            PromptTemplateValidator.validate_category_action_format(category, action)


class TestValidateVersionIncrement:
    """Test version increment validation"""

    def test_increment_from_1_0(self):
        """Test incrementing from version 1.0"""
        result = PromptTemplateValidator.validate_version_increment("1.0")
        assert result == "1.1"

    def test_increment_from_2_5(self):
        """Test incrementing from version 2.5"""
        result = PromptTemplateValidator.validate_version_increment("2.5")
        assert result == "2.6"

    def test_increment_from_9_9(self):
        """Test incrementing from version 9.9"""
        result = PromptTemplateValidator.validate_version_increment("9.9")
        assert result == "10.0"

    def test_increment_from_none(self):
        """Test incrementing from None returns 1.0"""
        result = PromptTemplateValidator.validate_version_increment(None)
        assert result == "1.0"

    def test_increment_from_empty_string(self):
        """Test incrementing from empty string returns 1.0"""
        result = PromptTemplateValidator.validate_version_increment("")
        assert result == "1.0"

    def test_increment_from_invalid_string(self):
        """Test incrementing from invalid string returns 1.0"""
        result = PromptTemplateValidator.validate_version_increment("invalid")
        assert result == "1.0"
        result = PromptTemplateValidator.validate_version_increment("abc.def")
        assert result == "1.0"

    def test_increment_preserves_one_decimal(self):
        """Test incrementing preserves one decimal place"""
        result = PromptTemplateValidator.validate_version_increment("1.0")
        assert result == "1.1"
        result = PromptTemplateValidator.validate_version_increment("1.9")
        assert result == "2.0"

    def test_increment_from_integer_string(self):
        """Test incrementing from integer string"""
        result = PromptTemplateValidator.validate_version_increment("3")
        assert result == "3.1"


class TestValidationErrorException:
    """Test PromptTemplateValidationError exception"""

    def test_validation_error_is_exception(self):
        """PromptTemplateValidationError is an Exception"""
        assert issubclass(PromptTemplateValidationError, Exception)

    def test_validation_error_can_be_raised(self):
        """PromptTemplateValidationError can be raised with message"""
        with pytest.raises(PromptTemplateValidationError, match="Test error message"):
            raise PromptTemplateValidationError("Test error message")
