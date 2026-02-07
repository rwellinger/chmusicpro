"""Tests for ImageValidator - Business logic unit tests"""

import pytest

from business.image_validator import ImageValidationError, ImageValidator


class TestValidatePrompt:
    """Test validate_prompt() - validates image prompt"""

    def test_valid_prompt(self):
        """Valid prompt with text"""
        ImageValidator.validate_prompt("A beautiful sunset")  # Should not raise

    def test_valid_long_prompt(self):
        """Valid long prompt"""
        prompt = "A detailed oil painting of a serene landscape with mountains and a lake"
        ImageValidator.validate_prompt(prompt)  # Should not raise

    def test_empty_prompt_invalid(self):
        """Empty string is invalid"""
        with pytest.raises(ImageValidationError, match="Prompt is required"):
            ImageValidator.validate_prompt("")

    def test_whitespace_only_prompt_invalid(self):
        """Whitespace-only prompt is invalid"""
        with pytest.raises(ImageValidationError, match="Prompt is required"):
            ImageValidator.validate_prompt("   ")

    def test_whitespace_with_tabs_invalid(self):
        """Tabs and spaces only is invalid"""
        with pytest.raises(ImageValidationError, match="Prompt is required"):
            ImageValidator.validate_prompt("\t\n  ")

    def test_none_prompt_invalid(self):
        """None prompt is invalid"""
        with pytest.raises(ImageValidationError, match="Prompt is required"):
            ImageValidator.validate_prompt(None)


class TestValidateSize:
    """Test validate_size() - validates image size parameter"""

    def test_valid_size(self):
        """Valid size specification"""
        ImageValidator.validate_size("1024x1024")  # Should not raise

    def test_valid_custom_size(self):
        """Valid custom size"""
        ImageValidator.validate_size("512x768")  # Should not raise

    def test_empty_size_invalid(self):
        """Empty string is invalid"""
        with pytest.raises(ImageValidationError, match="Size is required"):
            ImageValidator.validate_size("")

    def test_none_size_invalid(self):
        """None size is invalid"""
        with pytest.raises(ImageValidationError, match="Size is required"):
            ImageValidator.validate_size(None)


class TestValidateBulkDeleteCount:
    """Test validate_bulk_delete_count() - validates bulk delete limits"""

    def test_single_id_valid(self):
        """Single ID is valid"""
        image_ids = ["id1"]

        ImageValidator.validate_bulk_delete_count(image_ids)  # Should not raise

    def test_multiple_ids_valid(self):
        """Multiple IDs within limit is valid"""
        image_ids = [f"id{i}" for i in range(50)]

        ImageValidator.validate_bulk_delete_count(image_ids)  # Should not raise

    def test_max_limit_valid(self):
        """Exactly 100 IDs is valid"""
        image_ids = [f"id{i}" for i in range(100)]

        ImageValidator.validate_bulk_delete_count(image_ids)  # Should not raise

    def test_over_limit_invalid(self):
        """101 IDs exceeds limit"""
        image_ids = [f"id{i}" for i in range(101)]

        with pytest.raises(ImageValidationError, match="Too many images \\(max 100"):
            ImageValidator.validate_bulk_delete_count(image_ids)

    def test_way_over_limit_invalid(self):
        """Far over limit is invalid"""
        image_ids = [f"id{i}" for i in range(500)]

        with pytest.raises(ImageValidationError, match="Too many images \\(max 100"):
            ImageValidator.validate_bulk_delete_count(image_ids)

    def test_empty_list_invalid(self):
        """Empty list is invalid"""
        image_ids = []

        with pytest.raises(ImageValidationError, match="No image IDs provided"):
            ImageValidator.validate_bulk_delete_count(image_ids)

    def test_max_bulk_delete_constant(self):
        """Verify MAX_BULK_DELETE constant"""
        assert ImageValidator.MAX_BULK_DELETE == 100
