"""Unit tests for SketchController

Note: Success cases with Pydantic model_validate() are tested via integration tests.
These unit tests focus on error handling and edge cases.
"""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from api.controllers.sketch_controller import SketchController
from schemas.sketch_schemas import SketchUpdateRequest


@pytest.mark.unit
class TestSketchControllerGetById:
    """Test SketchController.get_sketch_by_id method"""

    def test_get_sketch_by_id_not_found(self, mock_db_session):
        """Test getting non-existent sketch"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        result, status_code = SketchController.get_sketch_by_id(mock_db_session, str(uuid4()))

        assert status_code == 404
        assert "error" in result

    def test_get_sketch_by_id_invalid_uuid(self, mock_db_session):
        """Test getting sketch with invalid UUID"""
        result, status_code = SketchController.get_sketch_by_id(mock_db_session, "invalid-uuid")

        assert status_code == 400
        assert "error" in result


@pytest.mark.unit
class TestSketchControllerUpdate:
    """Test SketchController.update_sketch method"""

    def test_update_sketch_not_found(self, mock_db_session):
        """Test updating non-existent sketch"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        update_data = SketchUpdateRequest(title="New Title")

        result, status_code = SketchController.update_sketch(
            db=mock_db_session, sketch_id=str(uuid4()), update_data=update_data
        )

        assert status_code == 404
        assert "error" in result

    def test_update_sketch_invalid_uuid(self, mock_db_session):
        """Test updating sketch with invalid UUID"""
        update_data = SketchUpdateRequest(title="New Title")

        result, status_code = SketchController.update_sketch(
            db=mock_db_session, sketch_id="invalid-uuid", update_data=update_data
        )

        assert status_code == 400
        assert "error" in result


@pytest.mark.unit
class TestSketchControllerDelete:
    """Test SketchController.delete_sketch method"""

    def test_delete_sketch_success(self, mock_db_session):
        """Test successful sketch deletion"""
        mock_sketch = MagicMock()
        mock_sketch.id = uuid4()

        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_sketch

        result, status_code = SketchController.delete_sketch(mock_db_session, str(mock_sketch.id))

        assert status_code == 200
        assert "message" in result
        mock_db_session.delete.assert_called_once_with(mock_sketch)
        mock_db_session.commit.assert_called_once()

    def test_delete_sketch_not_found(self, mock_db_session):
        """Test deleting non-existent sketch"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        result, status_code = SketchController.delete_sketch(mock_db_session, str(uuid4()))

        assert status_code == 404
        assert "error" in result

    def test_delete_sketch_invalid_uuid(self, mock_db_session):
        """Test deleting sketch with invalid UUID"""
        result, status_code = SketchController.delete_sketch(mock_db_session, "invalid-uuid")

        assert status_code == 400
        assert "error" in result
