"""
Unit tests for EquipmentNormalizer (pure functions).

CRITICAL: 100% coverage for pure business logic (per CLAUDE.md).
"""

from business.equipment_normalizer import EquipmentNormalizer


def test_normalize_field_trim_whitespace():
    """Test that leading/trailing whitespace is trimmed"""
    assert EquipmentNormalizer.normalize_field("  Logic Pro X  ") == "Logic Pro X"
    assert EquipmentNormalizer.normalize_field("\tTabbed\t") == "Tabbed"
    assert EquipmentNormalizer.normalize_field("\nNewline\n") == "Newline"


def test_normalize_field_empty_string():
    """Test that empty string returns None"""
    assert EquipmentNormalizer.normalize_field("") is None


def test_normalize_field_whitespace_only():
    """Test that whitespace-only string returns None"""
    assert EquipmentNormalizer.normalize_field("   ") is None
    assert EquipmentNormalizer.normalize_field("\t\t") is None
    assert EquipmentNormalizer.normalize_field("\n\n") is None


def test_normalize_field_none():
    """Test that None input returns None"""
    assert EquipmentNormalizer.normalize_field(None) is None


def test_normalize_field_preserves_internal_whitespace():
    """Test that internal whitespace is preserved"""
    assert EquipmentNormalizer.normalize_field("  Logic  Pro  X  ") == "Logic  Pro  X"


def test_normalize_equipment_data_all_fields():
    """Test normalization of all fields"""
    data = {
        "name": "  Logic Pro X  ",
        "description": "   ",
        "software_tags": "DAW, Apple",
        "plugin_tags": "",
        "manufacturer": "  Apple  ",
        "url": "https://www.apple.com",
        "username": "  user@example.com  ",
        "license_description": "Perpetual license",
        "system_requirements": "macOS 12+",
        "type": "Software",
        "status": "active",
        "license_management": "Online",
    }

    normalized = EquipmentNormalizer.normalize_equipment_data(data)

    assert normalized["name"] == "Logic Pro X"
    assert normalized["description"] is None  # Whitespace-only → None
    assert normalized["software_tags"] == "DAW, Apple"
    assert normalized["plugin_tags"] is None  # Empty → None
    assert normalized["manufacturer"] == "Apple"
    assert normalized["url"] == "https://www.apple.com"
    assert normalized["username"] == "user@example.com"
    assert normalized["license_description"] == "Perpetual license"
    assert normalized["system_requirements"] == "macOS 12+"
    assert normalized["type"] == "Software"
    assert normalized["status"] == "active"
    assert normalized["license_management"] == "Online"


def test_normalize_equipment_data_partial_fields():
    """Test normalization with only some fields present"""
    data = {
        "name": "  Plugin Name  ",
        "manufacturer": "Waves",
        "password": "secret123",  # Non-normalizable field
        "price": "99.99 USD",  # Non-normalizable field
    }

    normalized = EquipmentNormalizer.normalize_equipment_data(data)

    assert normalized["name"] == "Plugin Name"
    assert normalized["manufacturer"] == "Waves"
    assert normalized["password"] == "secret123"  # Unchanged
    assert normalized["price"] == "99.99 USD"  # Unchanged


def test_normalize_equipment_data_empty_dict():
    """Test normalization of empty dict"""
    data = {}
    normalized = EquipmentNormalizer.normalize_equipment_data(data)
    assert normalized == {}


def test_normalize_equipment_data_does_not_modify_original():
    """Test that original data dict is not modified"""
    data = {"name": "  Original  ", "description": "Test"}
    original_name = data["name"]
    original_description = data["description"]

    normalized = EquipmentNormalizer.normalize_equipment_data(data)

    assert data["name"] == original_name, "Original data should not be modified"
    assert data["description"] == original_description
    assert normalized["name"] == "Original"


def test_normalize_equipment_data_unicode():
    """Test normalization with unicode characters"""
    data = {
        "name": "  Ümlaut Sößware  ",
        "manufacturer": "  日本メーカー  ",
    }

    normalized = EquipmentNormalizer.normalize_equipment_data(data)

    assert normalized["name"] == "Ümlaut Sößware"
    assert normalized["manufacturer"] == "日本メーカー"


def test_normalize_equipment_data_none_values():
    """Test normalization with None values"""
    data = {
        "name": "Test",
        "description": None,
        "manufacturer": None,
    }

    normalized = EquipmentNormalizer.normalize_equipment_data(data)

    assert normalized["name"] == "Test"
    assert normalized["description"] is None
    assert normalized["manufacturer"] is None
