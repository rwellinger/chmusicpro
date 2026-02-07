"""
Unit tests for WorkshopNormalizer (pure functions).

CRITICAL: 100% coverage for pure business logic (per CLAUDE.md).
"""

from business.workshop_normalizer import WorkshopNormalizer


class TestNormalizeField:
    """Tests for normalize_field()"""

    def test_normalize_field_with_whitespace(self):
        """Test trimming whitespace"""
        assert WorkshopNormalizer.normalize_field("  hello  ") == "hello"
        assert WorkshopNormalizer.normalize_field("  test") == "test"
        assert WorkshopNormalizer.normalize_field("test  ") == "test"

    def test_normalize_field_empty_string(self):
        """Test converting empty string to None"""
        assert WorkshopNormalizer.normalize_field("") is None
        assert WorkshopNormalizer.normalize_field("   ") is None
        assert WorkshopNormalizer.normalize_field("\t\n  ") is None

    def test_normalize_field_none(self):
        """Test None input returns None"""
        assert WorkshopNormalizer.normalize_field(None) is None

    def test_normalize_field_valid_string(self):
        """Test valid strings remain unchanged"""
        assert WorkshopNormalizer.normalize_field("valid") == "valid"
        assert WorkshopNormalizer.normalize_field("multiple words") == "multiple words"

    def test_normalize_field_preserves_internal_whitespace(self):
        """Test that internal whitespace is preserved"""
        assert WorkshopNormalizer.normalize_field("  hello  world  ") == "hello  world"

    def test_normalize_field_special_characters(self):
        """Test strings with special characters"""
        assert WorkshopNormalizer.normalize_field("hello@world.com") == "hello@world.com"
        assert WorkshopNormalizer.normalize_field("Umlaut: ae oe ue") == "Umlaut: ae oe ue"

    def test_normalize_field_unicode(self):
        """Test strings with unicode characters"""
        assert WorkshopNormalizer.normalize_field("  Liebesgedicht  ") == "Liebesgedicht"
        assert WorkshopNormalizer.normalize_field("  Chanson d'amour  ") == "Chanson d'amour"


class TestNormalizeWorkshopData:
    """Tests for normalize_workshop_data()"""

    def test_normalize_all_fields(self):
        """Test normalizing all workshop fields"""
        data = {
            "title": "  Love Song Workshop  ",
            "connect_topic": "  First love in summer  ",
            "connect_inspirations": "   ",
            "collect_mindmap": "  Beach, sunset, waves  ",
            "collect_stories": "",
            "collect_words": "  ocean, breeze, warmth  ",
            "shape_structure": "  Verse-Chorus-Verse  ",
            "shape_rhymes": "\t\n",
            "shape_draft": "  First draft text  ",
        }

        result = WorkshopNormalizer.normalize_workshop_data(data)

        assert result["title"] == "Love Song Workshop"
        assert result["connect_topic"] == "First love in summer"
        assert result["connect_inspirations"] is None
        assert result["collect_mindmap"] == "Beach, sunset, waves"
        assert result["collect_stories"] is None
        assert result["collect_words"] == "ocean, breeze, warmth"
        assert result["shape_structure"] == "Verse-Chorus-Verse"
        assert result["shape_rhymes"] is None
        assert result["shape_draft"] == "First draft text"

    def test_normalize_partial_fields(self):
        """Test normalizing only some fields"""
        data = {
            "title": "  Test  ",
            "connect_topic": "topic",
        }

        result = WorkshopNormalizer.normalize_workshop_data(data)

        assert result["title"] == "Test"
        assert result["connect_topic"] == "topic"
        assert "collect_mindmap" not in result
        assert "shape_draft" not in result

    def test_normalize_empty_dict(self):
        """Test normalizing empty dict"""
        result = WorkshopNormalizer.normalize_workshop_data({})
        assert result == {}

    def test_normalize_no_normalization_needed(self):
        """Test data that doesn't need normalization"""
        data = {
            "title": "Valid Title",
            "connect_topic": "Valid Topic",
            "shape_draft": "Valid Draft",
        }

        result = WorkshopNormalizer.normalize_workshop_data(data)

        assert result["title"] == "Valid Title"
        assert result["connect_topic"] == "Valid Topic"
        assert result["shape_draft"] == "Valid Draft"

    def test_normalize_all_empty_strings(self):
        """Test all fields as empty strings"""
        data = {
            "title": "   ",
            "connect_topic": "",
            "connect_inspirations": "\t",
            "collect_mindmap": "  \n  ",
            "collect_stories": "",
            "collect_words": "   ",
            "shape_structure": "\t\n",
            "shape_rhymes": "",
            "shape_draft": "   ",
        }

        result = WorkshopNormalizer.normalize_workshop_data(data)

        for key in data:
            assert result[key] is None, f"{key} should be None"

    def test_normalize_all_none(self):
        """Test all fields as None"""
        data = {
            "title": None,
            "connect_topic": None,
            "connect_inspirations": None,
            "collect_mindmap": None,
            "collect_stories": None,
            "collect_words": None,
            "shape_structure": None,
            "shape_rhymes": None,
            "shape_draft": None,
        }

        result = WorkshopNormalizer.normalize_workshop_data(data)

        for key in data:
            assert result[key] is None, f"{key} should remain None"

    def test_normalize_preserves_non_normalizable_fields(self):
        """Test that non-normalizable fields are preserved unchanged"""
        data = {
            "title": "  Test  ",
            "current_phase": "connect",
            "draft_language": "EN",
            "some_other_field": 123,
        }

        result = WorkshopNormalizer.normalize_workshop_data(data)

        assert result["title"] == "Test"
        assert result["current_phase"] == "connect"
        assert result["draft_language"] == "EN"
        assert result["some_other_field"] == 123

    def test_normalize_does_not_mutate_original(self):
        """Test that original dict is not mutated"""
        original = {
            "title": "  Test  ",
            "connect_topic": "   ",
        }

        result = WorkshopNormalizer.normalize_workshop_data(original)

        assert original["title"] == "  Test  "
        assert original["connect_topic"] == "   "
        assert result["title"] == "Test"
        assert result["connect_topic"] is None
