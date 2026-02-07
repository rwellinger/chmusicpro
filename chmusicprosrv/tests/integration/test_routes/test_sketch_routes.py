"""Integration tests for Sketch API with Pydantic Validation

These tests validate the complete controller flow including Pydantic model validation.
Unlike unit tests that mock everything, these tests ensure that:
1. Pydantic models validate correctly
2. Response structures match schema definitions
3. Database models convert to Pydantic models properly
"""

from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from api.controllers.sketch_controller import SketchController
from schemas.sketch_schemas import SketchCreateRequest, SketchListResponse, SketchResponse


@pytest.fixture
def mock_sketch_db_model():
    """Mock SongSketch database model instance"""
    mock = MagicMock(
        spec=[
            "id",
            "title",
            "lyrics",
            "prompt",
            "tags",
            "workflow",
            "description_long",
            "description_short",
            "description_tags",
            "info",
            "project_id",
            "project_name",
            "sketch_type",
            "created_at",
            "updated_at",
        ]
    )
    mock.id = uuid4()
    mock.title = "Test Sketch"
    mock.lyrics = "[Verse 1]\nTest lyrics"
    mock.prompt = "upbeat pop"
    mock.tags = "pop, test"
    mock.workflow = "draft"
    mock.description_long = None
    mock.description_short = None
    mock.description_tags = None
    mock.info = None
    mock.project_id = None
    mock.project_name = None
    mock.sketch_type = "manual"
    mock.created_at = datetime.now()
    mock.updated_at = None
    return mock


@pytest.mark.integration
class TestSketchControllerIntegration:
    """Integration tests for SketchController with Pydantic validation"""

    def test_list_sketches_returns_correct_pagination_structure(self, mock_db_session, mock_sketch_db_model):
        """
        Test that SketchController.get_sketches returns correct pagination structure.
        This catches the bug where pagination was returned as flat fields instead of nested.
        """
        with patch("db.sketch_service.sketch_service.get_sketches_paginated") as mock_get:
            mock_get.return_value = {"items": [mock_sketch_db_model], "total": 1}

            result, status_code = SketchController.get_sketches(
                db=mock_db_session, limit=20, offset=0, search="", workflow=None
            )

            assert status_code == 200

            # This is the critical test - pagination must be nested!
            assert "pagination" in result, "Response must have 'pagination' key (not flat total/limit/offset)"
            assert "data" in result, "Response must have 'data' key"

            # Verify pagination metadata structure
            pagination = result["pagination"]
            assert "total" in pagination
            assert "limit" in pagination
            assert "offset" in pagination
            assert "has_more" in pagination

            # Verify pagination values
            assert pagination["total"] == 1
            assert pagination["limit"] == 20
            assert pagination["offset"] == 0
            assert pagination["has_more"] is False

            # Verify data structure
            assert len(result["data"]) == 1
            assert result["data"][0]["id"] == str(mock_sketch_db_model.id)

    def test_list_sketches_pydantic_validation_passes(self, mock_db_session, mock_sketch_db_model):
        """Test that the response passes Pydantic validation"""
        with patch("db.sketch_service.sketch_service.get_sketches_paginated") as mock_get:
            mock_get.return_value = {"items": [mock_sketch_db_model], "total": 1}

            result, status_code = SketchController.get_sketches(
                db=mock_db_session, limit=20, offset=0, search="", workflow=None
            )

            assert status_code == 200

            # This validates the response can be parsed by Pydantic (would throw ValidationError if wrong)
            validated = SketchListResponse.model_validate(result)
            assert validated.pagination.total == 1
            assert len(validated.data) == 1

    def test_list_sketches_has_more_flag_calculation(self, mock_db_session, mock_sketch_db_model):
        """Test has_more flag is correctly calculated"""
        with patch("db.sketch_service.sketch_service.get_sketches_paginated") as mock_get:
            # Return 20 items but total is 50
            mock_get.return_value = {"items": [mock_sketch_db_model] * 20, "total": 50}

            result, status_code = SketchController.get_sketches(
                db=mock_db_session, limit=20, offset=0, search="", workflow=None
            )

            assert status_code == 200
            # has_more should be True because 0 + 20 < 50
            assert result["pagination"]["has_more"] is True

            # Test with last page
            mock_get.return_value = {"items": [mock_sketch_db_model] * 10, "total": 50}
            result, status_code = SketchController.get_sketches(
                db=mock_db_session, limit=20, offset=40, search="", workflow=None
            )

            assert status_code == 200
            # has_more should be False because 40 + 10 = 50 (no more)
            assert result["pagination"]["has_more"] is False

    def test_create_sketch_pydantic_validation(self, mock_db_session, mock_sketch_db_model):
        """Test that create_sketch response passes Pydantic validation"""
        sketch_data = SketchCreateRequest(
            title="Test Sketch", lyrics="Test lyrics", prompt="upbeat pop", tags="pop, test"
        )

        with patch("db.sketch_service.sketch_service.create_sketch") as mock_create:
            mock_create.return_value = mock_sketch_db_model

            result, status_code = SketchController.create_sketch(sketch_data=sketch_data, db=mock_db_session)

            assert status_code == 201
            assert "data" in result
            assert "message" in result

            # Validate that data can be parsed as SketchResponse
            validated = SketchResponse.model_validate(result["data"])
            assert str(validated.id) == str(mock_sketch_db_model.id)

    def test_list_sketches_empty_results(self, mock_db_session):
        """Test list sketches with no results"""
        with patch("db.sketch_service.sketch_service.get_sketches_paginated") as mock_get:
            mock_get.return_value = {"items": [], "total": 0}

            result, status_code = SketchController.get_sketches(
                db=mock_db_session, limit=20, offset=0, search="", workflow=None
            )

            assert status_code == 200
            assert result["pagination"]["total"] == 0
            assert result["pagination"]["has_more"] is False
            assert len(result["data"]) == 0
