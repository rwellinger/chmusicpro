"""
Unit tests for Workshop Pydantic schema validators (pure validation).

Tests field_validators in WorkshopCreateRequest, WorkshopUpdateRequest, WorkshopResponse.
"""

import pytest
from pydantic import ValidationError

from schemas.workshop_schemas import (
    WorkshopCreateRequest,
    WorkshopResponse,
    WorkshopUpdateRequest,
)


class TestWorkshopCreateRequest:
    """Test WorkshopCreateRequest validators"""

    def test_valid_create(self):
        """Valid creation data should pass"""
        data = {"title": "Love Song Workshop"}
        request = WorkshopCreateRequest(**data)
        assert request.title == "Love Song Workshop"
        assert request.connect_topic is None
        assert request.draft_language == "EN"

    def test_valid_create_with_all_fields(self):
        """Valid creation with all fields"""
        data = {
            "title": "Workshop",
            "connect_topic": "First love",
            "draft_language": "DE",
        }
        request = WorkshopCreateRequest(**data)
        assert request.title == "Workshop"
        assert request.connect_topic == "First love"
        assert request.draft_language == "DE"

    def test_missing_title(self):
        """Missing title should raise ValidationError"""
        with pytest.raises(ValidationError):
            WorkshopCreateRequest()

    def test_empty_title(self):
        """Empty title should raise ValidationError (min_length=1)"""
        with pytest.raises(ValidationError):
            WorkshopCreateRequest(title="")

    def test_title_too_long(self):
        """Title > 200 chars should raise ValidationError"""
        with pytest.raises(ValidationError):
            WorkshopCreateRequest(title="x" * 201)

    def test_valid_draft_languages(self):
        """All valid draft languages should pass"""
        for lang in ["EN", "DE", "FR", "IT", "ES"]:
            request = WorkshopCreateRequest(title="Test", draft_language=lang)
            assert request.draft_language == lang

    def test_invalid_draft_language(self):
        """Invalid draft language should raise ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            WorkshopCreateRequest(title="Test", draft_language="JP")
        assert "draft_language must be one of" in str(exc_info.value)

    def test_none_draft_language(self):
        """None draft_language should pass"""
        request = WorkshopCreateRequest(title="Test", draft_language=None)
        assert request.draft_language is None


class TestWorkshopUpdateRequest:
    """Test WorkshopUpdateRequest validators"""

    def test_valid_phase_values(self):
        """All valid phases should pass"""
        for phase in ["connect", "collect", "shape", "completed"]:
            request = WorkshopUpdateRequest(current_phase=phase)
            assert request.current_phase == phase

    def test_invalid_phase(self):
        """Invalid phase should raise ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            WorkshopUpdateRequest(current_phase="invalid")
        assert "current_phase must be one of" in str(exc_info.value)

    def test_none_phase(self):
        """None phase should pass (optional)"""
        request = WorkshopUpdateRequest(current_phase=None)
        assert request.current_phase is None

    def test_valid_draft_languages(self):
        """All valid draft languages should pass"""
        for lang in ["EN", "DE", "FR", "IT", "ES"]:
            request = WorkshopUpdateRequest(draft_language=lang)
            assert request.draft_language == lang

    def test_invalid_draft_language(self):
        """Invalid draft language should raise ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            WorkshopUpdateRequest(draft_language="JP")
        assert "draft_language must be one of" in str(exc_info.value)

    def test_none_draft_language(self):
        """None draft_language should pass"""
        request = WorkshopUpdateRequest(draft_language=None)
        assert request.draft_language is None

    def test_empty_update(self):
        """Empty update (no fields) should pass"""
        request = WorkshopUpdateRequest()
        assert request.title is None
        assert request.current_phase is None

    def test_title_max_length(self):
        """Title > 200 chars should raise ValidationError"""
        with pytest.raises(ValidationError):
            WorkshopUpdateRequest(title="x" * 201)

    def test_title_min_length(self):
        """Empty title should raise ValidationError (min_length=1)"""
        with pytest.raises(ValidationError):
            WorkshopUpdateRequest(title="")


class TestWorkshopResponse:
    """Test WorkshopResponse validators"""

    def test_valid_phases(self):
        """All valid phases should pass"""
        base_data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "Test",
            "created_at": "2024-01-01T00:00:00Z",
        }
        for phase in ["connect", "collect", "shape", "completed"]:
            response = WorkshopResponse(**{**base_data, "current_phase": phase})
            assert response.current_phase == phase

    def test_invalid_phase(self):
        """Invalid phase should raise ValidationError"""
        data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "Test",
            "current_phase": "invalid",
            "created_at": "2024-01-01T00:00:00Z",
        }
        with pytest.raises(ValidationError) as exc_info:
            WorkshopResponse(**data)
        assert "current_phase must be one of" in str(exc_info.value)

    def test_uuid_serialization(self):
        """UUIDs should serialize to strings"""
        data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "Test",
            "current_phase": "connect",
            "created_at": "2024-01-01T00:00:00Z",
            "exported_sketch_id": "660e8400-e29b-41d4-a716-446655440000",
        }
        response = WorkshopResponse(**data)
        dumped = response.model_dump()
        assert dumped["id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert dumped["exported_sketch_id"] == "660e8400-e29b-41d4-a716-446655440000"

    def test_none_exported_sketch_id(self):
        """None exported_sketch_id should serialize to None"""
        data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "Test",
            "current_phase": "connect",
            "created_at": "2024-01-01T00:00:00Z",
            "exported_sketch_id": None,
        }
        response = WorkshopResponse(**data)
        dumped = response.model_dump()
        assert dumped["exported_sketch_id"] is None
