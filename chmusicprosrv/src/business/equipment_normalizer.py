"""
Equipment Data Normalizer (Pure Functions).

CRITICAL: This module contains PURE BUSINESS LOGIC (100% unit-testable).
- NO database operations
- NO file system operations
- NO external API calls
- ONLY data transformations

These functions are 100% covered by unit tests in tests/test_equipment_normalizer.py
"""


class EquipmentNormalizer:
    """Pure functions for equipment data normalization"""

    @staticmethod
    def normalize_field(value: str | None) -> str | None:
        """
        Normalize string field: trim whitespace, convert empty strings to None.

        Args:
            value: String value to normalize

        Returns:
            Normalized string or None

        Examples:
            >>> EquipmentNormalizer.normalize_field("  Logic Pro X  ")
            "Logic Pro X"
            >>> EquipmentNormalizer.normalize_field("")
            None
            >>> EquipmentNormalizer.normalize_field("   ")
            None
            >>> EquipmentNormalizer.normalize_field(None)
            None
        """
        if value is None:
            return None
        normalized = value.strip()
        return normalized if normalized else None

    @staticmethod
    def normalize_equipment_data(data: dict) -> dict:
        """
        Normalize all string fields in equipment data.

        Args:
            data: Equipment data dict

        Returns:
            Normalized equipment data dict

        Example:
            >>> data = {
            ...     "name": "  Logic Pro X  ",
            ...     "description": "",
            ...     "manufacturer": "Apple",
            ...     "type": "Software"
            ... }
            >>> normalized = EquipmentNormalizer.normalize_equipment_data(data)
            >>> normalized["name"]
            "Logic Pro X"
            >>> normalized["description"]
            None
        """
        normalizable_fields = [
            "name",
            "description",
            "software_tags",
            "plugin_tags",
            "manufacturer",
            "url",
            "username",
            "license_description",
            "system_requirements",
            "type",
            "status",
            "license_management",
        ]

        normalized = data.copy()
        for field in normalizable_fields:
            if field in normalized:
                normalized[field] = EquipmentNormalizer.normalize_field(normalized[field])

        return normalized
