"""Suno Template Normalizer - Pure functions for data normalization and style prompt building"""


class SunoTemplateNormalizer:
    """Normalize suno template data (pure functions)"""

    @staticmethod
    def normalize_field(value: str | None) -> str | None:
        """Normalize string field: trim whitespace, convert empty strings to None"""
        if value is None:
            return None
        normalized = value.strip()
        return normalized if normalized else None

    @staticmethod
    def normalize_template_data(data: dict) -> dict:
        """Normalize all string fields in template data dict"""
        normalizable_fields = [
            "title",
            "original_lyrics",
            "enhanced_lyrics",
            "genre",
            "vocal_type",
            "instruments",
            "mood",
            "mix_character",
            "style_prompt",
        ]

        normalized = data.copy()

        for field in normalizable_fields:
            if field in normalized:
                normalized[field] = SunoTemplateNormalizer.normalize_field(normalized[field])

        return normalized

    @staticmethod
    def build_style_prompt(
        genre: str | None = None,
        bpm: int | None = None,
        vocal_type: str | None = None,
        instruments: str | None = None,
        mood: str | None = None,
        mix_character: str | None = None,
        is_instrumental: bool = False,
    ) -> str:
        """
        Build a comma-separated style prompt from individual fields.

        Pure function - no dependencies, fully unit-testable.

        Args:
            genre: e.g. "Indie Pop"
            bpm: e.g. 120
            vocal_type: e.g. "warm male vocals"
            instruments: e.g. "acoustic guitar, piano"
            mood: e.g. "bright and uplifting"
            mix_character: e.g. "clean mix"
            is_instrumental: Whether to add "Instrumental" marker

        Returns:
            Comma-separated style prompt string
        """
        parts = []

        if genre:
            parts.append(genre.strip())
        if bpm:
            parts.append(f"{bpm} BPM")
        if is_instrumental:
            parts.append("Instrumental")
        elif vocal_type:
            parts.append(vocal_type.strip())
        if instruments:
            parts.append(instruments.strip())
        if mood:
            parts.append(mood.strip())
        if mix_character:
            parts.append(mix_character.strip())

        return ", ".join(parts)
