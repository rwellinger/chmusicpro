"""Tests for ImageTransformer - Business logic unit tests"""

from datetime import datetime
from unittest.mock import Mock

from business.image_transformer import ImageTransformer


class TestGeneratePromptHash:
    """Test generate_prompt_hash() - MD5 hash generation"""

    def test_hash_generation(self):
        """Generate hash from prompt"""
        prompt = "A beautiful sunset"

        hash_value = ImageTransformer.generate_prompt_hash(prompt)

        assert len(hash_value) == 10
        assert hash_value.isalnum()  # Only alphanumeric characters

    def test_hash_deterministic(self):
        """Same prompt produces same hash"""
        prompt = "A beautiful sunset"

        hash1 = ImageTransformer.generate_prompt_hash(prompt)
        hash2 = ImageTransformer.generate_prompt_hash(prompt)

        assert hash1 == hash2

    def test_hash_different_prompts(self):
        """Different prompts produce different hashes"""
        prompt1 = "A beautiful sunset"
        prompt2 = "A stormy ocean"

        hash1 = ImageTransformer.generate_prompt_hash(prompt1)
        hash2 = ImageTransformer.generate_prompt_hash(prompt2)

        assert hash1 != hash2

    def test_hash_empty_prompt(self):
        """Hash generation works with empty string"""
        prompt = ""

        hash_value = ImageTransformer.generate_prompt_hash(prompt)

        assert len(hash_value) == 10


class TestGenerateFilename:
    """Test generate_filename() - filename construction"""

    def test_filename_with_timestamp(self):
        """Generate filename with provided timestamp"""
        prompt = "A sunset"
        timestamp = 1234567890

        filename = ImageTransformer.generate_filename(prompt, timestamp)

        assert filename.endswith("_1234567890.png")
        assert len(filename) == 10 + 1 + 10 + 4  # hash_timestamp.png

    def test_filename_format(self):
        """Filename follows correct format"""
        prompt = "A sunset"
        timestamp = 1234567890

        filename = ImageTransformer.generate_filename(prompt, timestamp)

        parts = filename.split("_")
        assert len(parts) == 2
        assert parts[0].isalnum()  # Hash part
        assert parts[1] == "1234567890.png"  # Timestamp + extension

    def test_filename_deterministic(self):
        """Same prompt and timestamp produce same filename"""
        prompt = "A sunset"
        timestamp = 1234567890

        filename1 = ImageTransformer.generate_filename(prompt, timestamp)
        filename2 = ImageTransformer.generate_filename(prompt, timestamp)

        assert filename1 == filename2

    def test_filename_without_timestamp_uses_current_time(self):
        """Filename without timestamp uses current time"""
        prompt = "A sunset"

        filename = ImageTransformer.generate_filename(prompt)

        # Should have format: hash_timestamp.png
        assert filename.endswith(".png")
        assert "_" in filename


class TestGetDisplayUrl:
    """Test get_display_url() - URL transformation for text overlay"""

    def test_display_url_without_overlay(self):
        """No text overlay - returns original URL"""
        local_url = "/images/photo.png"

        display_url = ImageTransformer.get_display_url(local_url, has_text_overlay=False)

        assert display_url == "/images/photo.png"

    def test_display_url_with_overlay(self):
        """Text overlay exists - returns overlay URL"""
        local_url = "/images/photo.png"

        display_url = ImageTransformer.get_display_url(local_url, has_text_overlay=True)

        assert display_url == "/images/photo_with_text.png"

    def test_display_url_already_has_overlay_suffix(self):
        """URL already has _with_text suffix - returns as is"""
        local_url = "/images/photo_with_text.png"

        display_url = ImageTransformer.get_display_url(local_url, has_text_overlay=True)

        assert display_url == "/images/photo_with_text.png"  # Not doubled

    def test_display_url_complex_path(self):
        """Complex path with subdirectories"""
        local_url = "/api/images/2024/01/photo_abc123.png"

        display_url = ImageTransformer.get_display_url(local_url, has_text_overlay=True)

        assert display_url == "/api/images/2024/01/photo_abc123_with_text.png"


class TestTransformImageToApiFormat:
    """Test transform_image_to_api_format() - database to API format"""

    def create_mock_image(self, **kwargs):
        """Helper to create mock GeneratedImage object"""
        defaults = {
            "id": "test-id-123",
            "user_prompt": "Test prompt",
            "prompt": "Enhanced test prompt",
            "enhanced_prompt": None,
            "size": "1024x1024",
            "filename": "test.png",
            "local_url": "/images/test.png",
            "model_used": "dall-e-3",
            "title": "Test Image",
            "tags": "test,image",
            "text_overlay_metadata": None,
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
            "updated_at": datetime(2024, 1, 2, 12, 0, 0),
            "prompt_hash": "abc123def4",
            "artistic_style": "photorealistic",
            "composition": "landscape",
            "lighting": "natural",
            "color_palette": "vibrant",
            "detail_level": "highly-detailed",
            "file_path": "/path/to/test.png",
            "project_references": [],  # Empty list for project references
        }
        defaults.update(kwargs)

        mock = Mock()
        for key, value in defaults.items():
            setattr(mock, key, value)
        return mock

    def test_transform_basic_image(self):
        """Transform basic image without text overlay"""
        image = self.create_mock_image()

        result = ImageTransformer.transform_image_to_api_format(image)

        assert result["id"] == "test-id-123"
        assert result["user_prompt"] == "Test prompt"
        assert result["prompt"] == "Enhanced test prompt"
        assert result["size"] == "1024x1024"
        assert result["filename"] == "test.png"
        assert result["url"] == "/images/test.png"
        assert result["display_url"] == "/images/test.png"  # No overlay
        assert result["model_used"] == "dall-e-3"
        assert result["title"] == "Test Image"
        assert result["tags"] == "test,image"

    def test_transform_image_with_text_overlay(self):
        """Transform image with text overlay metadata"""
        image = self.create_mock_image(text_overlay_metadata={"text": "Overlay"})

        result = ImageTransformer.transform_image_to_api_format(image)

        assert result["url"] == "/images/test.png"  # Original
        assert result["display_url"] == "/images/test_with_text.png"  # Overlay version
        assert result["text_overlay_metadata"] == {"text": "Overlay"}

    def test_transform_include_file_path(self):
        """Include file_path when requested"""
        image = self.create_mock_image()

        result = ImageTransformer.transform_image_to_api_format(image, include_file_path=True)

        assert result["file_path"] == "/path/to/test.png"

    def test_transform_exclude_file_path(self):
        """Exclude file_path by default"""
        image = self.create_mock_image()

        result = ImageTransformer.transform_image_to_api_format(image, include_file_path=False)

        assert "file_path" not in result

    def test_transform_datetime_isoformat(self):
        """Datetime fields converted to ISO format"""
        image = self.create_mock_image()

        result = ImageTransformer.transform_image_to_api_format(image)

        assert result["created_at"] == "2024-01-01T12:00:00"
        assert result["updated_at"] == "2024-01-02T12:00:00"

    def test_transform_none_datetime(self):
        """None datetime fields handled correctly"""
        image = self.create_mock_image(created_at=None, updated_at=None)

        result = ImageTransformer.transform_image_to_api_format(image)

        assert result["created_at"] is None
        assert result["updated_at"] is None

    def test_transform_style_fields(self):
        """All style fields included"""
        image = self.create_mock_image()

        result = ImageTransformer.transform_image_to_api_format(image)

        assert result["artistic_style"] == "photorealistic"
        assert result["composition"] == "landscape"
        assert result["lighting"] == "natural"
        assert result["color_palette"] == "vibrant"
        assert result["detail_level"] == "highly-detailed"
