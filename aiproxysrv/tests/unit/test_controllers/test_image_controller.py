"""Unit tests for ImageController (without infrastructure dependencies)"""

from unittest.mock import MagicMock

import pytest

from api.controllers.image_controller import ImageController
from business.image_orchestrator import ImageGenerationError


@pytest.mark.unit
class TestImageControllerGetImagesForTextOverlay:
    """Test ImageController.get_images_for_text_overlay method"""

    def test_get_images_for_text_overlay_success(self, mocker):
        """Test successful retrieval of images for text overlay"""
        mocker.patch.object(ImageController, "__init__", return_value=None)
        controller = ImageController()
        controller.orchestrator = MagicMock()

        expected_result = {
            "images": [
                {
                    "id": "123",
                    "title": "Test Image",
                    "file_path": "/path/to/image.png",
                }
            ],
            "total": 1,
        }

        controller.orchestrator.get_images_for_text_overlay.return_value = expected_result

        result, status_code = controller.get_images_for_text_overlay()

        assert status_code == 200
        assert result == expected_result
        controller.orchestrator.get_images_for_text_overlay.assert_called_once()

    def test_get_images_for_text_overlay_business_error(self, mocker):
        """Test handling of business layer error"""
        mocker.patch.object(ImageController, "__init__", return_value=None)
        controller = ImageController()
        controller.orchestrator = MagicMock()

        controller.orchestrator.get_images_for_text_overlay.side_effect = ImageGenerationError("Database error")

        result, status_code = controller.get_images_for_text_overlay()

        assert status_code == 500
        assert "error" in result
        assert "Database error" in result["error"]

    def test_get_images_for_text_overlay_unexpected_error(self, mocker):
        """Test handling of unexpected error"""
        mocker.patch.object(ImageController, "__init__", return_value=None)
        controller = ImageController()
        controller.orchestrator = MagicMock()

        controller.orchestrator.get_images_for_text_overlay.side_effect = Exception("Unexpected failure")

        result, status_code = controller.get_images_for_text_overlay()

        assert status_code == 500
        assert "error" in result
        assert "Internal server error" in result["error"]


@pytest.mark.unit
class TestImageControllerAddTextOverlay:
    """Test ImageController.add_text_overlay method"""

    def test_add_text_overlay_missing_image(self, mocker):
        """Test text overlay when source image not found"""
        mocker.patch.object(ImageController, "__init__", return_value=None)
        controller = ImageController()
        controller.orchestrator = MagicMock()

        # Mock orchestrator to raise error for missing image
        controller.orchestrator.add_text_overlay_to_image.side_effect = ImageGenerationError(
            "Source image not found: nonexistent"
        )

        result, status_code = controller.add_text_overlay(
            image_id="nonexistent",
            user_id="user123",
            title="Test Title",
        )

        assert status_code == 500
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_add_text_overlay_missing_file_path(self, mocker):
        """Test text overlay when image has no file path"""
        mocker.patch.object(ImageController, "__init__", return_value=None)
        controller = ImageController()
        controller.orchestrator = MagicMock()

        # Mock orchestrator to raise error for missing file path
        controller.orchestrator.add_text_overlay_to_image.side_effect = ImageGenerationError(
            "Source image file path not found"
        )

        result, status_code = controller.add_text_overlay(
            image_id="123",
            user_id="user123",
            title="Test Title",
        )

        assert status_code == 500
        assert "error" in result
        assert "file path not found" in result["error"].lower()

    def test_add_text_overlay_business_error(self, mocker):
        """Test text overlay with business layer error"""
        mocker.patch.object(ImageController, "__init__", return_value=None)
        controller = ImageController()
        controller.orchestrator = MagicMock()

        controller.orchestrator.add_text_overlay_to_image.side_effect = ImageGenerationError("Database error")

        result, status_code = controller.add_text_overlay(
            image_id="123",
            user_id="user123",
            title="Test Title",
        )

        assert status_code == 500
        assert "error" in result
        assert "Database error" in result["error"]

    def test_add_text_overlay_unexpected_error(self, mocker):
        """Test text overlay with unexpected error"""
        mocker.patch.object(ImageController, "__init__", return_value=None)
        controller = ImageController()
        controller.orchestrator = MagicMock()

        controller.orchestrator.add_text_overlay_to_image.side_effect = ValueError("Invalid input")

        result, status_code = controller.add_text_overlay(
            image_id="123",
            user_id="user123",
            title="Test Title",
        )

        assert status_code == 500
        assert "error" in result
        assert "Internal server error" in result["error"]


@pytest.mark.unit
class TestImageControllerDeleteImage:
    """Test ImageController.delete_image method"""

    def test_delete_image_success(self, mocker):
        """Test successful image deletion"""
        mocker.patch.object(ImageController, "__init__", return_value=None)
        controller = ImageController()
        controller.orchestrator = MagicMock()

        controller.orchestrator.delete_single_image.return_value = True

        result, status_code = controller.delete_image("123")

        assert status_code == 200
        assert result["message"] == "Image deleted successfully"

    def test_delete_image_not_found(self, mocker):
        """Test deletion of non-existent image"""
        mocker.patch.object(ImageController, "__init__", return_value=None)
        controller = ImageController()
        controller.orchestrator = MagicMock()

        controller.orchestrator.delete_single_image.return_value = False

        result, status_code = controller.delete_image("nonexistent")

        assert status_code == 404
        assert "error" in result

    def test_delete_image_business_error(self, mocker):
        """Test deletion with business layer error"""
        mocker.patch.object(ImageController, "__init__", return_value=None)
        controller = ImageController()
        controller.orchestrator = MagicMock()

        controller.orchestrator.delete_single_image.side_effect = ImageGenerationError("Database error")

        result, status_code = controller.delete_image("123")

        assert status_code == 500
        assert "error" in result


@pytest.mark.unit
class TestImageControllerBulkDelete:
    """Test ImageController.bulk_delete_images method"""

    def test_bulk_delete_no_ids(self, mocker):
        """Test bulk delete with empty ID list"""
        mocker.patch.object(ImageController, "__init__", return_value=None)
        controller = ImageController()
        controller.orchestrator = MagicMock()

        result, status_code = controller.bulk_delete_images([])

        assert status_code == 400
        assert "error" in result
        assert "No image IDs" in result["error"]

    def test_bulk_delete_too_many_ids(self, mocker):
        """Test bulk delete with too many IDs (>100)"""
        mocker.patch.object(ImageController, "__init__", return_value=None)
        controller = ImageController()
        controller.orchestrator = MagicMock()

        # Create 101 IDs
        too_many_ids = [f"id_{i}" for i in range(101)]

        result, status_code = controller.bulk_delete_images(too_many_ids)

        assert status_code == 400
        assert "error" in result
        assert "Too many images" in result["error"]

    def test_bulk_delete_all_success(self, mocker):
        """Test bulk delete with all deletions successful"""
        mocker.patch.object(ImageController, "__init__", return_value=None)
        controller = ImageController()
        controller.orchestrator = MagicMock()

        controller.orchestrator.bulk_delete_images.return_value = {
            "summary": {"deleted": 3, "not_found": 0, "errors": 0},
            "details": [],
        }

        result, status_code = controller.bulk_delete_images(["id1", "id2", "id3"])

        assert status_code == 200
        assert result["summary"]["deleted"] == 3

    def test_bulk_delete_partial_success(self, mocker):
        """Test bulk delete with partial success (multi-status)"""
        mocker.patch.object(ImageController, "__init__", return_value=None)
        controller = ImageController()
        controller.orchestrator = MagicMock()

        controller.orchestrator.bulk_delete_images.return_value = {
            "summary": {"deleted": 2, "not_found": 1, "errors": 0},
            "details": [],
        }

        result, status_code = controller.bulk_delete_images(["id1", "id2", "id3"])

        assert status_code == 207  # Multi-status
        assert result["summary"]["deleted"] == 2

    def test_bulk_delete_all_not_found(self, mocker):
        """Test bulk delete with all IDs not found"""
        mocker.patch.object(ImageController, "__init__", return_value=None)
        controller = ImageController()
        controller.orchestrator = MagicMock()

        controller.orchestrator.bulk_delete_images.return_value = {
            "summary": {"deleted": 0, "not_found": 3, "errors": 0},
            "details": [],
        }

        result, status_code = controller.bulk_delete_images(["id1", "id2", "id3"])

        assert status_code == 404
        assert result["summary"]["deleted"] == 0

    def test_bulk_delete_all_errors(self, mocker):
        """Test bulk delete with all deletions failing"""
        mocker.patch.object(ImageController, "__init__", return_value=None)
        controller = ImageController()
        controller.orchestrator = MagicMock()

        controller.orchestrator.bulk_delete_images.return_value = {
            "summary": {"deleted": 0, "not_found": 0, "errors": 3},
            "details": [],
        }

        result, status_code = controller.bulk_delete_images(["id1", "id2", "id3"])

        assert status_code == 400
        assert result["summary"]["errors"] == 3


@pytest.mark.unit
class TestImageControllerUpdateMetadata:
    """Test ImageController.update_image_metadata method"""

    def test_update_metadata_success(self, mocker):
        """Test successful metadata update"""
        mocker.patch.object(ImageController, "__init__", return_value=None)
        controller = ImageController()
        controller.orchestrator = MagicMock()

        expected_result = {
            "id": "123",
            "title": "Updated Title",
            "tags": "tag1,tag2",
        }

        controller.orchestrator.update_image_metadata.return_value = expected_result

        result, status_code = controller.update_image_metadata("123", title="Updated Title", tags="tag1,tag2")

        assert status_code == 200
        assert result == expected_result

    def test_update_metadata_not_found(self, mocker):
        """Test update metadata for non-existent image"""
        mocker.patch.object(ImageController, "__init__", return_value=None)
        controller = ImageController()
        controller.orchestrator = MagicMock()

        controller.orchestrator.update_image_metadata.return_value = None

        result, status_code = controller.update_image_metadata("nonexistent", title="New Title")

        assert status_code == 404
        assert "error" in result
