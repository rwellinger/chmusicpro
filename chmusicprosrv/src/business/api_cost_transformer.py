"""API Cost Transformer - Business logic for cost data transformations

Pure functions for transforming and processing cost data.
No database or infrastructure dependencies.
"""

from typing import Any

from db.models import ApiCostMonthly


class ApiCostTransformer:
    """Transformer for API cost data (pure functions, unit-testable)"""

    @staticmethod
    def transform_to_dict(result: ApiCostMonthly) -> dict[str, Any]:
        """
        Transform DB model to dictionary with type conversions

        Args:
            result: ApiCostMonthly database model

        Returns:
            Dict with cost data (Decimal → float, field mapping)
        """
        return {
            "year": result.year,
            "month": result.month,
            "total": float(result.total_cost),
            "image": float(result.image_cost),
            "chat": float(result.chat_cost),
            "currency": result.currency,
            "organization_id": result.organization_id,
            "breakdown": result.line_items,
            "bucket_count": result.bucket_count,
            "is_finalized": result.is_finalized,
            "last_updated_at": result.last_updated_at,
        }

    @staticmethod
    def apply_cost_defaults(costs: dict[str, Any]) -> dict[str, Any]:
        """
        Apply default values to cost data

        Args:
            costs: Cost data dictionary (may be incomplete)

        Returns:
            Cost data with defaults applied
        """
        return {
            "total": costs["total"],  # Required field
            "image": costs.get("image", 0),
            "chat": costs.get("chat", 0),
            "currency": costs.get("currency", "usd"),
            "breakdown": costs.get("breakdown", {}),
            "bucket_count": costs.get("bucket_count"),
        }

    @staticmethod
    def validate_cost_data(costs: dict[str, Any]) -> tuple[bool, str | None]:
        """
        Validate cost data structure

        Args:
            costs: Cost data dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        if "total" not in costs:
            return False, "Missing required field: total"

        if not isinstance(costs["total"], (int, float)):
            return False, "Field 'total' must be numeric"

        if costs["total"] < 0:
            return False, "Field 'total' cannot be negative"

        return True, None

    @staticmethod
    def format_all_time_costs(total: float, image: float, chat: float, currency: str = "usd") -> dict[str, Any]:
        """
        Format all-time aggregated costs to response format (pure function)

        Args:
            total: Total cost across all months
            image: Image cost across all months
            chat: Chat cost across all months
            currency: Currency code (default: 'usd')

        Returns:
            Dict with formatted all-time cost data
        """
        return {
            "year": None,  # All-time has no specific year
            "month": None,  # All-time has no specific month
            "total": total,
            "image": image,
            "chat": chat,
            "currency": currency,
            "organization_id": None,
            "breakdown": {},  # No line-item breakdown for aggregated data
            "bucket_count": None,
            "is_finalized": True,  # All-time data is always considered finalized
        }
