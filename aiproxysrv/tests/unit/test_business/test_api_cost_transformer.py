"""Unit tests for ApiCostTransformer

Pure unit tests for business logic (no DB, no infrastructure).
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from business.api_cost_transformer import ApiCostTransformer
from db.models import ApiCostMonthly


@pytest.mark.unit
class TestApiCostTransformerTransformToDict:
    """Test ApiCostTransformer.transform_to_dict method"""

    def test_transform_to_dict_complete_data(self):
        """Test transformation with all fields populated"""
        # Arrange
        mock_result = MagicMock(spec=ApiCostMonthly)
        mock_result.year = 2025
        mock_result.month = 10
        mock_result.total_cost = Decimal("123.45")
        mock_result.image_cost = Decimal("50.00")
        mock_result.chat_cost = Decimal("73.45")
        mock_result.currency = "usd"
        mock_result.organization_id = "org-123"
        mock_result.line_items = {"dalle3": 50.00, "gpt4": 73.45}
        mock_result.bucket_count = 2
        mock_result.is_finalized = True
        mock_result.last_updated_at = datetime(2025, 11, 1, 12, 0, 0)

        # Act
        result = ApiCostTransformer.transform_to_dict(mock_result)

        # Assert
        assert result["year"] == 2025
        assert result["month"] == 10
        assert result["total"] == 123.45  # Decimal → float
        assert result["image"] == 50.00  # Decimal → float
        assert result["chat"] == 73.45  # Decimal → float
        assert result["currency"] == "usd"
        assert result["organization_id"] == "org-123"
        assert result["breakdown"] == {"dalle3": 50.00, "gpt4": 73.45}
        assert result["bucket_count"] == 2
        assert result["is_finalized"] is True
        assert result["last_updated_at"] == datetime(2025, 11, 1, 12, 0, 0)

    def test_transform_to_dict_decimal_conversion(self):
        """Test that Decimal values are converted to float"""
        # Arrange
        mock_result = MagicMock(spec=ApiCostMonthly)
        mock_result.year = 2025
        mock_result.month = 10
        mock_result.total_cost = Decimal("99.999")
        mock_result.image_cost = Decimal("49.50")
        mock_result.chat_cost = Decimal("50.499")
        mock_result.currency = "usd"
        mock_result.organization_id = None
        mock_result.line_items = {}
        mock_result.bucket_count = 1
        mock_result.is_finalized = False
        mock_result.last_updated_at = datetime(2025, 10, 25, 10, 0, 0)

        # Act
        result = ApiCostTransformer.transform_to_dict(mock_result)

        # Assert - verify float type
        assert isinstance(result["total"], float)
        assert isinstance(result["image"], float)
        assert isinstance(result["chat"], float)
        assert result["total"] == 99.999
        assert result["image"] == 49.50
        assert result["chat"] == 50.499

    def test_transform_to_dict_none_values(self):
        """Test transformation with None values"""
        # Arrange
        mock_result = MagicMock(spec=ApiCostMonthly)
        mock_result.year = 2025
        mock_result.month = 10
        mock_result.total_cost = Decimal("100.00")
        mock_result.image_cost = Decimal("0.00")
        mock_result.chat_cost = Decimal("100.00")
        mock_result.currency = "usd"
        mock_result.organization_id = None  # Can be None
        mock_result.line_items = {}
        mock_result.bucket_count = None  # Can be None
        mock_result.is_finalized = False
        mock_result.last_updated_at = datetime(2025, 10, 25, 10, 0, 0)

        # Act
        result = ApiCostTransformer.transform_to_dict(mock_result)

        # Assert
        assert result["organization_id"] is None
        assert result["bucket_count"] is None


@pytest.mark.unit
class TestApiCostTransformerApplyDefaults:
    """Test ApiCostTransformer.apply_cost_defaults method"""

    def test_apply_defaults_complete_data(self):
        """Test applying defaults with all fields present"""
        # Arrange
        costs = {
            "total": 150.00,
            "image": 60.00,
            "chat": 90.00,
            "currency": "usd",
            "breakdown": {"dalle3": 60.00, "gpt4o": 90.00},
            "bucket_count": 2,
        }

        # Act
        result = ApiCostTransformer.apply_cost_defaults(costs)

        # Assert
        assert result["total"] == 150.00
        assert result["image"] == 60.00
        assert result["chat"] == 90.00
        assert result["currency"] == "usd"
        assert result["breakdown"] == {"dalle3": 60.00, "gpt4o": 90.00}
        assert result["bucket_count"] == 2

    def test_apply_defaults_minimal_data(self):
        """Test applying defaults with only required field (total)"""
        # Arrange
        costs = {"total": 100.00}

        # Act
        result = ApiCostTransformer.apply_cost_defaults(costs)

        # Assert
        assert result["total"] == 100.00
        assert result["image"] == 0  # Default
        assert result["chat"] == 0  # Default
        assert result["currency"] == "usd"  # Default
        assert result["breakdown"] == {}  # Default
        assert result["bucket_count"] is None  # Default

    def test_apply_defaults_partial_data(self):
        """Test applying defaults with some fields missing"""
        # Arrange
        costs = {
            "total": 200.00,
            "image": 80.00,
            # chat missing → should default to 0
            "currency": "eur",
            # breakdown missing → should default to {}
        }

        # Act
        result = ApiCostTransformer.apply_cost_defaults(costs)

        # Assert
        assert result["total"] == 200.00
        assert result["image"] == 80.00
        assert result["chat"] == 0  # Default
        assert result["currency"] == "eur"
        assert result["breakdown"] == {}  # Default
        assert result["bucket_count"] is None  # Default

    def test_apply_defaults_zero_values(self):
        """Test that explicit zero values are preserved (not replaced by defaults)"""
        # Arrange
        costs = {
            "total": 100.00,
            "image": 0,  # Explicit zero
            "chat": 100.00,
            "bucket_count": 0,  # Explicit zero
        }

        # Act
        result = ApiCostTransformer.apply_cost_defaults(costs)

        # Assert
        assert result["image"] == 0  # Explicit zero preserved
        assert result["bucket_count"] == 0  # Explicit zero preserved


@pytest.mark.unit
class TestApiCostTransformerValidateCostData:
    """Test ApiCostTransformer.validate_cost_data method"""

    def test_validate_complete_valid_data(self):
        """Test validation with valid complete data"""
        # Arrange
        costs = {"total": 150.00, "image": 60.00, "chat": 90.00}

        # Act
        is_valid, error = ApiCostTransformer.validate_cost_data(costs)

        # Assert
        assert is_valid is True
        assert error is None

    def test_validate_missing_total(self):
        """Test validation fails when total is missing"""
        # Arrange
        costs = {"image": 60.00, "chat": 90.00}

        # Act
        is_valid, error = ApiCostTransformer.validate_cost_data(costs)

        # Assert
        assert is_valid is False
        assert error == "Missing required field: total"

    def test_validate_total_not_numeric(self):
        """Test validation fails when total is not numeric"""
        # Arrange
        costs = {"total": "not-a-number"}

        # Act
        is_valid, error = ApiCostTransformer.validate_cost_data(costs)

        # Assert
        assert is_valid is False
        assert error == "Field 'total' must be numeric"

    def test_validate_negative_total(self):
        """Test validation fails when total is negative"""
        # Arrange
        costs = {"total": -50.00}

        # Act
        is_valid, error = ApiCostTransformer.validate_cost_data(costs)

        # Assert
        assert is_valid is False
        assert error == "Field 'total' cannot be negative"

    def test_validate_zero_total(self):
        """Test validation passes with zero total (valid edge case)"""
        # Arrange
        costs = {"total": 0}

        # Act
        is_valid, error = ApiCostTransformer.validate_cost_data(costs)

        # Assert
        assert is_valid is True
        assert error is None

    def test_validate_integer_total(self):
        """Test validation passes with integer total"""
        # Arrange
        costs = {"total": 100}

        # Act
        is_valid, error = ApiCostTransformer.validate_cost_data(costs)

        # Assert
        assert is_valid is True
        assert error is None
