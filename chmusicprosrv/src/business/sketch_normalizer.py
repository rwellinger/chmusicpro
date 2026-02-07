"""Sketch Normalizer - Pure functions for data normalization"""


class SketchNormalizer:
    """Normalize sketch data (pure functions)"""

    @staticmethod
    def normalize_field(value: str | None) -> str | None:
        """
        Normalize string field: trim whitespace, convert empty strings to None

        Pure function - no dependencies, fully unit-testable

        Args:
            value: String value or None

        Returns:
            Normalized string or None

        Examples:
            "  hello  " -> "hello"
            "   " -> None
            "" -> None
            None -> None
            "valid" -> "valid"
        """
        if value is None:
            return None

        # Strip whitespace
        normalized = value.strip()

        # Convert empty string to None
        return normalized if normalized else None

    @staticmethod
    def normalize_sketch_data(data: dict) -> dict:
        """
        Normalize all string fields in sketch data dict

        Pure function - no dependencies, fully unit-testable

        Args:
            data: Dict with sketch fields (may contain None values)

        Returns:
            Dict with normalized string fields

        Example:
            {"title": "  Test  ", "lyrics": "  ", "prompt": "pop"}
            -> {"title": "Test", "lyrics": None, "prompt": "pop"}
        """
        # Fields that should be normalized (trim + empty -> None)
        normalizable_fields = [
            "title",
            "lyrics",
            "prompt",
            "tags",
            "description_long",
            "description_short",
            "description_tags",
            "info",
        ]

        normalized = data.copy()

        for field in normalizable_fields:
            if field in normalized:
                normalized[field] = SketchNormalizer.normalize_field(normalized[field])

        return normalized
