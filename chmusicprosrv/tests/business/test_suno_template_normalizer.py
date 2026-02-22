"""
Unit tests for SunoTemplateNormalizer (pure functions).

CRITICAL: 100% coverage for pure business logic (per CLAUDE.md).
"""

from business.suno_template_normalizer import SunoTemplateNormalizer


class TestNormalizeField:
    """Tests for normalize_field()"""

    def test_normalize_field_with_whitespace(self):
        assert SunoTemplateNormalizer.normalize_field("  hello  ") == "hello"

    def test_normalize_field_empty_string(self):
        assert SunoTemplateNormalizer.normalize_field("") is None
        assert SunoTemplateNormalizer.normalize_field("   ") is None

    def test_normalize_field_none(self):
        assert SunoTemplateNormalizer.normalize_field(None) is None

    def test_normalize_field_valid_string(self):
        assert SunoTemplateNormalizer.normalize_field("valid") == "valid"


class TestNormalizeTemplateData:
    """Tests for normalize_template_data()"""

    def test_normalize_all_fields(self):
        data = {
            "title": "  My Song  ",
            "original_lyrics": "  Hello world  ",
            "enhanced_lyrics": "  [Intro]\nHello  ",
            "genre": "  Indie Pop  ",
            "vocal_type": "  warm male vocals  ",
            "instruments": "  guitar, piano  ",
            "mood": "  bright  ",
            "mix_character": "  clean mix  ",
            "style_prompt": "  Indie Pop, 120 BPM  ",
        }

        result = SunoTemplateNormalizer.normalize_template_data(data)

        assert result["title"] == "My Song"
        assert result["original_lyrics"] == "Hello world"
        assert result["enhanced_lyrics"] == "[Intro]\nHello"
        assert result["genre"] == "Indie Pop"
        assert result["vocal_type"] == "warm male vocals"
        assert result["instruments"] == "guitar, piano"
        assert result["mood"] == "bright"
        assert result["mix_character"] == "clean mix"
        assert result["style_prompt"] == "Indie Pop, 120 BPM"

    def test_normalize_empty_strings_to_none(self):
        data = {
            "title": "   ",
            "genre": "",
            "mood": "\t\n",
        }
        result = SunoTemplateNormalizer.normalize_template_data(data)
        assert result["title"] is None
        assert result["genre"] is None
        assert result["mood"] is None

    def test_normalize_preserves_non_normalizable_fields(self):
        data = {
            "title": "  Test  ",
            "bpm": 120,
            "is_instrumental": True,
        }
        result = SunoTemplateNormalizer.normalize_template_data(data)
        assert result["title"] == "Test"
        assert result["bpm"] == 120
        assert result["is_instrumental"] is True

    def test_normalize_does_not_mutate_original(self):
        original = {"title": "  Test  ", "genre": "   "}
        result = SunoTemplateNormalizer.normalize_template_data(original)
        assert original["title"] == "  Test  "
        assert result["title"] == "Test"


class TestBuildStylePrompt:
    """Tests for build_style_prompt()"""

    def test_build_full_prompt(self):
        result = SunoTemplateNormalizer.build_style_prompt(
            genre="Indie Pop",
            bpm=120,
            vocal_type="warm male vocals",
            instruments="acoustic guitar, piano",
            mood="bright and uplifting",
            mix_character="clean mix",
        )
        assert result == "Indie Pop, 120 BPM, warm male vocals, acoustic guitar, piano, bright and uplifting, clean mix"

    def test_build_minimal_prompt(self):
        result = SunoTemplateNormalizer.build_style_prompt(genre="Rock")
        assert result == "Rock"

    def test_build_instrumental_prompt(self):
        result = SunoTemplateNormalizer.build_style_prompt(
            genre="EDM",
            bpm=140,
            is_instrumental=True,
            instruments="synth, bass",
        )
        assert result == "EDM, 140 BPM, Instrumental, synth, bass"

    def test_build_instrumental_excludes_vocal_type(self):
        result = SunoTemplateNormalizer.build_style_prompt(
            genre="Ambient",
            vocal_type="female vocals",
            is_instrumental=True,
        )
        assert "female vocals" not in result
        assert "Instrumental" in result

    def test_build_empty_prompt(self):
        result = SunoTemplateNormalizer.build_style_prompt()
        assert result == ""

    def test_build_prompt_trims_whitespace(self):
        result = SunoTemplateNormalizer.build_style_prompt(
            genre="  Pop  ",
            mood="  happy  ",
        )
        assert result == "Pop, happy"

    def test_build_only_bpm(self):
        result = SunoTemplateNormalizer.build_style_prompt(bpm=90)
        assert result == "90 BPM"
