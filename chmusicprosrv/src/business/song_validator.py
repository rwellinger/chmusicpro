"""Song Validator - Pure validation functions for song operations (testable business logic)"""

from typing import Any


class SongValidationError(Exception):
    """Raised when song validation fails"""

    pass


class SongValidator:
    """Validation logic for song operations (pure functions, 100% testable)"""

    # Business rules as constants
    ALLOWED_UPDATE_FIELDS = ["title", "tags", "workflow"]
    VALID_RATINGS = [0, 1, None]
    MAX_BULK_DELETE = 100

    @staticmethod
    def validate_update_fields(update_data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate and filter update fields to only allowed fields

        Pure function - no DB, no file system, fully unit-testable

        Args:
            update_data: Dict with fields to update

        Returns:
            Dict with only allowed fields

        Raises:
            SongValidationError: If no valid fields provided

        Example:
            data = {"title": "New Song", "tags": "rock", "invalid_field": "value"}
            filtered = SongValidator.validate_update_fields(data)
            # {"title": "New Song", "tags": "rock"}
        """
        filtered_data = {k: v for k, v in update_data.items() if k in SongValidator.ALLOWED_UPDATE_FIELDS}

        if not filtered_data:
            raise SongValidationError("No valid fields provided for update")

        return filtered_data

    @staticmethod
    def validate_rating(rating: int | None) -> None:
        """
        Validate rating value

        Pure function - no DB, no file system, fully unit-testable

        Args:
            rating: Rating value to validate (0, 1, or None)

        Raises:
            SongValidationError: If rating is not valid

        Example:
            SongValidator.validate_rating(1)  # OK
            SongValidator.validate_rating(None)  # OK
            SongValidator.validate_rating(5)  # Raises SongValidationError
        """
        if rating is not None and rating not in SongValidator.VALID_RATINGS:
            raise SongValidationError("Rating must be null, 0 (thumbs down), or 1 (thumbs up)")

    @staticmethod
    def validate_bulk_delete_count(song_ids: list[str]) -> None:
        """
        Validate bulk delete request count

        Pure function - no DB, no file system, fully unit-testable

        Args:
            song_ids: List of song IDs to delete

        Raises:
            SongValidationError: If list is empty or exceeds max count

        Example:
            SongValidator.validate_bulk_delete_count(["id1", "id2"])  # OK
            SongValidator.validate_bulk_delete_count([])  # Raises SongValidationError
            SongValidator.validate_bulk_delete_count([f"id{i}" for i in range(101)])  # Raises
        """
        if not song_ids:
            raise SongValidationError("No song IDs provided")

        if len(song_ids) > SongValidator.MAX_BULK_DELETE:
            raise SongValidationError(f"Too many songs (max {SongValidator.MAX_BULK_DELETE} per request)")
