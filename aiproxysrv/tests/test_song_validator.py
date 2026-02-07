"""Tests for SongValidator - Business logic unit tests"""

import pytest

from business.song_validator import SongValidationError, SongValidator


class TestValidateUpdateFields:
    """Test validate_update_fields() - filters allowed fields"""

    def test_valid_single_field(self):
        """Single valid field"""
        data = {"title": "New Song"}

        filtered = SongValidator.validate_update_fields(data)

        assert filtered == {"title": "New Song"}

    def test_valid_multiple_fields(self):
        """Multiple valid fields"""
        data = {"title": "New Song", "tags": "rock,pop", "workflow": "draft"}

        filtered = SongValidator.validate_update_fields(data)

        assert filtered == {"title": "New Song", "tags": "rock,pop", "workflow": "draft"}

    def test_filter_invalid_fields(self):
        """Mix of valid and invalid fields - filters invalid"""
        data = {"title": "New Song", "invalid_field": "value", "another_invalid": 123}

        filtered = SongValidator.validate_update_fields(data)

        assert filtered == {"title": "New Song"}

    def test_all_invalid_fields_raises_error(self):
        """Only invalid fields - raises error"""
        data = {"invalid_field": "value", "another_invalid": 123}

        with pytest.raises(SongValidationError, match="No valid fields provided"):
            SongValidator.validate_update_fields(data)

    def test_empty_dict_raises_error(self):
        """Empty dict - raises error"""
        data = {}

        with pytest.raises(SongValidationError, match="No valid fields provided"):
            SongValidator.validate_update_fields(data)

    def test_allowed_fields_constant(self):
        """Verify ALLOWED_UPDATE_FIELDS constant"""
        assert SongValidator.ALLOWED_UPDATE_FIELDS == ["title", "tags", "workflow"]


class TestValidateRating:
    """Test validate_rating() - validates rating values"""

    def test_rating_none_valid(self):
        """Rating None is valid"""
        SongValidator.validate_rating(None)  # Should not raise

    def test_rating_zero_valid(self):
        """Rating 0 (thumbs down) is valid"""
        SongValidator.validate_rating(0)  # Should not raise

    def test_rating_one_valid(self):
        """Rating 1 (thumbs up) is valid"""
        SongValidator.validate_rating(1)  # Should not raise

    def test_rating_negative_invalid(self):
        """Negative rating is invalid"""
        with pytest.raises(SongValidationError, match="Rating must be null, 0 .* or 1"):
            SongValidator.validate_rating(-1)

    def test_rating_two_invalid(self):
        """Rating 2 is invalid"""
        with pytest.raises(SongValidationError, match="Rating must be null, 0 .* or 1"):
            SongValidator.validate_rating(2)

    def test_rating_large_number_invalid(self):
        """Large rating number is invalid"""
        with pytest.raises(SongValidationError, match="Rating must be null, 0 .* or 1"):
            SongValidator.validate_rating(100)

    def test_valid_ratings_constant(self):
        """Verify VALID_RATINGS constant"""
        assert SongValidator.VALID_RATINGS == [0, 1, None]


class TestValidateBulkDeleteCount:
    """Test validate_bulk_delete_count() - validates bulk delete limits"""

    def test_single_id_valid(self):
        """Single ID is valid"""
        song_ids = ["id1"]

        SongValidator.validate_bulk_delete_count(song_ids)  # Should not raise

    def test_multiple_ids_valid(self):
        """Multiple IDs within limit is valid"""
        song_ids = [f"id{i}" for i in range(50)]

        SongValidator.validate_bulk_delete_count(song_ids)  # Should not raise

    def test_max_limit_valid(self):
        """Exactly 100 IDs is valid"""
        song_ids = [f"id{i}" for i in range(100)]

        SongValidator.validate_bulk_delete_count(song_ids)  # Should not raise

    def test_over_limit_invalid(self):
        """101 IDs exceeds limit"""
        song_ids = [f"id{i}" for i in range(101)]

        with pytest.raises(SongValidationError, match="Too many songs \\(max 100"):
            SongValidator.validate_bulk_delete_count(song_ids)

    def test_way_over_limit_invalid(self):
        """Far over limit is invalid"""
        song_ids = [f"id{i}" for i in range(500)]

        with pytest.raises(SongValidationError, match="Too many songs \\(max 100"):
            SongValidator.validate_bulk_delete_count(song_ids)

    def test_empty_list_invalid(self):
        """Empty list is invalid"""
        song_ids = []

        with pytest.raises(SongValidationError, match="No song IDs provided"):
            SongValidator.validate_bulk_delete_count(song_ids)

    def test_max_bulk_delete_constant(self):
        """Verify MAX_BULK_DELETE constant"""
        assert SongValidator.MAX_BULK_DELETE == 100
