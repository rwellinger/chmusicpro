"""Image Validator - Pure validation functions for image operations (testable business logic)"""


class ImageValidationError(Exception):
    """Raised when image validation fails"""

    pass


class ImageValidator:
    """Validation logic for image operations (pure functions, 100% testable)"""

    MAX_BULK_DELETE = 100

    @staticmethod
    def validate_prompt(prompt: str) -> None:
        """
        Validate image generation prompt

        Pure function - no DB, no file system, fully unit-testable

        Args:
            prompt: Image prompt to validate

        Raises:
            ImageValidationError: If prompt is invalid

        Example:
            ImageValidator.validate_prompt("A beautiful sunset")  # OK
            ImageValidator.validate_prompt("   ")  # Raises ImageValidationError (only whitespace)
            ImageValidator.validate_prompt("")  # Raises ImageValidationError (empty)
        """
        if not prompt or not prompt.strip():
            raise ImageValidationError("Prompt is required")

    @staticmethod
    def validate_size(size: str) -> None:
        """
        Validate image size parameter

        Pure function - no DB, no file system, fully unit-testable

        Args:
            size: Image size specification

        Raises:
            ImageValidationError: If size is invalid

        Example:
            ImageValidator.validate_size("1024x1024")  # OK
            ImageValidator.validate_size("")  # Raises ImageValidationError
            ImageValidator.validate_size(None)  # Raises ImageValidationError
        """
        if not size:
            raise ImageValidationError("Size is required")

    @staticmethod
    def validate_bulk_delete_count(image_ids: list[str]) -> None:
        """
        Validate bulk delete request count

        Pure function - no DB, no file system, fully unit-testable

        Args:
            image_ids: List of image IDs to delete

        Raises:
            ImageValidationError: If list is empty or exceeds max count

        Example:
            ImageValidator.validate_bulk_delete_count(["id1", "id2"])  # OK
            ImageValidator.validate_bulk_delete_count([])  # Raises ImageValidationError
            ImageValidator.validate_bulk_delete_count([f"id{i}" for i in range(101)])  # Raises
        """
        if not image_ids:
            raise ImageValidationError("No image IDs provided")

        if len(image_ids) > ImageValidator.MAX_BULK_DELETE:
            raise ImageValidationError(f"Too many images (max {ImageValidator.MAX_BULK_DELETE} per request)")
