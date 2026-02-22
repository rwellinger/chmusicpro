"""
Unit tests for Suno Template Pydantic schema validators (pure validation).
"""

import pytest
from pydantic import ValidationError

from schemas.suno_template_schemas import (
    SunoTemplateCreateRequest,
    SunoTemplateUpdateRequest,
)


class TestSunoTemplateCreateRequest:
    """Test SunoTemplateCreateRequest validators"""

    def test_valid_create_minimal(self):
        request = SunoTemplateCreateRequest(title="My Template")
        assert request.title == "My Template"
        assert request.template_type == "song"
        assert request.is_instrumental is False

    def test_valid_create_full(self):
        request = SunoTemplateCreateRequest(
            title="EDM Template",
            template_type="instrumental",
            genre="EDM",
            bpm=140,
            instruments="synth, bass",
            mood="energetic",
            is_instrumental=True,
        )
        assert request.template_type == "instrumental"
        assert request.bpm == 140
        assert request.is_instrumental is True

    def test_missing_title(self):
        with pytest.raises(ValidationError):
            SunoTemplateCreateRequest()

    def test_empty_title(self):
        with pytest.raises(ValidationError):
            SunoTemplateCreateRequest(title="")

    def test_title_too_long(self):
        with pytest.raises(ValidationError):
            SunoTemplateCreateRequest(title="x" * 501)

    def test_invalid_template_type(self):
        with pytest.raises(ValidationError):
            SunoTemplateCreateRequest(title="Test", template_type="invalid")

    def test_valid_template_types(self):
        for t in ["song", "instrumental"]:
            request = SunoTemplateCreateRequest(title="Test", template_type=t)
            assert request.template_type == t

    def test_bpm_range_valid(self):
        for bpm in [40, 120, 300]:
            request = SunoTemplateCreateRequest(title="Test", bpm=bpm)
            assert request.bpm == bpm

    def test_bpm_too_low(self):
        with pytest.raises(ValidationError):
            SunoTemplateCreateRequest(title="Test", bpm=39)

    def test_bpm_too_high(self):
        with pytest.raises(ValidationError):
            SunoTemplateCreateRequest(title="Test", bpm=301)


class TestSunoTemplateUpdateRequest:
    """Test SunoTemplateUpdateRequest validators"""

    def test_all_optional(self):
        request = SunoTemplateUpdateRequest()
        assert request.title is None
        assert request.template_type is None
        assert request.bpm is None

    def test_partial_update(self):
        request = SunoTemplateUpdateRequest(genre="Rock", bpm=130)
        assert request.genre == "Rock"
        assert request.bpm == 130
        assert request.title is None

    def test_invalid_template_type(self):
        with pytest.raises(ValidationError):
            SunoTemplateUpdateRequest(template_type="invalid")

    def test_none_template_type_allowed(self):
        request = SunoTemplateUpdateRequest(template_type=None)
        assert request.template_type is None
