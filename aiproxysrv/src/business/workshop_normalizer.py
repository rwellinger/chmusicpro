"""Workshop Normalizer - Pure functions for data normalization"""


class WorkshopNormalizer:
    """Normalize workshop data (pure functions)"""

    @staticmethod
    def normalize_field(value: str | None) -> str | None:
        """
        Normalize string field: trim whitespace, convert empty strings to None

        Pure function - no dependencies, fully unit-testable

        Args:
            value: String value or None

        Returns:
            Normalized string or None
        """
        if value is None:
            return None

        normalized = value.strip()
        return normalized if normalized else None

    @staticmethod
    def normalize_workshop_data(data: dict) -> dict:
        """
        Normalize all string fields in workshop data dict

        Pure function - no dependencies, fully unit-testable

        Args:
            data: Dict with workshop fields (may contain None values)

        Returns:
            Dict with normalized string fields
        """
        normalizable_fields = [
            "title",
            "connect_topic",
            "connect_inspirations",
            "collect_mindmap",
            "collect_stories",
            "collect_words",
            "shape_structure",
            "shape_rhymes",
            "shape_draft",
        ]

        normalized = data.copy()

        for field in normalizable_fields:
            if field in normalized:
                normalized[field] = WorkshopNormalizer.normalize_field(normalized[field])

        return normalized
