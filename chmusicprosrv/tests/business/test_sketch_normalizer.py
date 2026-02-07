"""Unit tests for SketchNormalizer"""

from business.sketch_normalizer import SketchNormalizer


class TestNormalizeField:
    """Tests for normalize_field()"""

    def test_normalize_field_with_whitespace(self):
        """Test trimming whitespace"""
        assert SketchNormalizer.normalize_field("  hello  ") == "hello"
        assert SketchNormalizer.normalize_field("  test") == "test"
        assert SketchNormalizer.normalize_field("test  ") == "test"

    def test_normalize_field_empty_string(self):
        """Test converting empty string to None"""
        assert SketchNormalizer.normalize_field("") is None
        assert SketchNormalizer.normalize_field("   ") is None
        assert SketchNormalizer.normalize_field("\t\n  ") is None

    def test_normalize_field_none(self):
        """Test None input returns None"""
        assert SketchNormalizer.normalize_field(None) is None

    def test_normalize_field_valid_string(self):
        """Test valid strings remain unchanged"""
        assert SketchNormalizer.normalize_field("valid") == "valid"
        assert SketchNormalizer.normalize_field("multiple words") == "multiple words"
        assert SketchNormalizer.normalize_field("with-dashes_and_underscores") == "with-dashes_and_underscores"

    def test_normalize_field_special_characters(self):
        """Test strings with special characters"""
        assert SketchNormalizer.normalize_field("hello@world.com") == "hello@world.com"
        assert SketchNormalizer.normalize_field("$$$") == "$$$"
        assert SketchNormalizer.normalize_field("a&b") == "a&b"


class TestNormalizeSketchData:
    """Tests for normalize_sketch_data()"""

    def test_normalize_sketch_data_all_fields(self):
        """Test normalizing all fields"""
        data = {
            "title": "  My Title  ",
            "lyrics": "   ",
            "tags": "pop,rock",
            "prompt": "  energetic  ",
            "description_long": "  Long desc  ",
            "description_short": "",
            "description_tags": "tag1,tag2",
            "info": None,
        }

        result = SketchNormalizer.normalize_sketch_data(data)

        assert result["title"] == "My Title"
        assert result["lyrics"] is None  # Empty string -> None
        assert result["tags"] == "pop,rock"
        assert result["prompt"] == "energetic"
        assert result["description_long"] == "Long desc"
        assert result["description_short"] is None  # Empty string -> None
        assert result["description_tags"] == "tag1,tag2"
        assert result["info"] is None

    def test_normalize_sketch_data_partial_fields(self):
        """Test normalizing only some fields"""
        data = {
            "title": "  Test  ",
            "prompt": "pop",
        }

        result = SketchNormalizer.normalize_sketch_data(data)

        assert result["title"] == "Test"
        assert result["prompt"] == "pop"
        assert "lyrics" not in result
        assert "tags" not in result

    def test_normalize_sketch_data_empty_dict(self):
        """Test normalizing empty dict"""
        data = {}
        result = SketchNormalizer.normalize_sketch_data(data)
        assert result == {}

    def test_normalize_sketch_data_no_normalization_needed(self):
        """Test data that doesn't need normalization"""
        data = {
            "title": "Valid Title",
            "lyrics": "Valid Lyrics",
            "prompt": "pop",
            "tags": "rock,jazz",
        }

        result = SketchNormalizer.normalize_sketch_data(data)

        assert result["title"] == "Valid Title"
        assert result["lyrics"] == "Valid Lyrics"
        assert result["prompt"] == "pop"
        assert result["tags"] == "rock,jazz"

    def test_normalize_sketch_data_all_empty_strings(self):
        """Test all fields as empty strings"""
        data = {
            "title": "   ",
            "lyrics": "",
            "tags": "\t",
            "prompt": "  \n  ",
            "description_long": "",
            "description_short": "   ",
            "description_tags": "\t\n",
            "info": "",
        }

        result = SketchNormalizer.normalize_sketch_data(data)

        # All should be None
        assert result["title"] is None
        assert result["lyrics"] is None
        assert result["tags"] is None
        assert result["prompt"] is None
        assert result["description_long"] is None
        assert result["description_short"] is None
        assert result["description_tags"] is None
        assert result["info"] is None

    def test_normalize_sketch_data_all_none(self):
        """Test all fields as None"""
        data = {
            "title": None,
            "lyrics": None,
            "tags": None,
            "prompt": None,
            "description_long": None,
            "description_short": None,
            "description_tags": None,
            "info": None,
        }

        result = SketchNormalizer.normalize_sketch_data(data)

        # All should remain None
        assert result["title"] is None
        assert result["lyrics"] is None
        assert result["tags"] is None
        assert result["prompt"] is None
        assert result["description_long"] is None
        assert result["description_short"] is None
        assert result["description_tags"] is None
        assert result["info"] is None

    def test_normalize_sketch_data_preserves_non_normalizable_fields(self):
        """Test that non-normalizable fields are preserved"""
        data = {
            "title": "  Test  ",
            "workflow": "draft",  # Not in normalizable_fields
            "some_other_field": 123,  # Not in normalizable_fields
        }

        result = SketchNormalizer.normalize_sketch_data(data)

        assert result["title"] == "Test"
        assert result["workflow"] == "draft"  # Unchanged
        assert result["some_other_field"] == 123  # Unchanged

    def test_normalize_sketch_data_does_not_mutate_original(self):
        """Test that original dict is not mutated"""
        original = {
            "title": "  Test  ",
            "lyrics": "   ",
        }

        result = SketchNormalizer.normalize_sketch_data(original)

        # Original should be unchanged
        assert original["title"] == "  Test  "
        assert original["lyrics"] == "   "

        # Result should be normalized
        assert result["title"] == "Test"
        assert result["lyrics"] is None
