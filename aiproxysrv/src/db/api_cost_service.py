"""API Cost Service - Database operations for API cost caching (Repository Layer)

Pure CRUD operations, no business logic.
Business logic is in business/api_cost_transformer.py
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from business.api_cost_transformer import ApiCostTransformer
from db.models import ApiCostMonthly
from utils.logger import logger


class ApiCostService:
    """Service for API cost database operations"""

    def get_cached_month(
        self, db: Session, provider: str, year: int, month: int, organization_id: str | None = None
    ) -> dict[str, Any] | None:
        """
        Get cached costs for specific month

        Args:
            db: Database session
            provider: 'openai' or 'mureka'
            year: Year (e.g., 2025)
            month: Month (1-12)
            organization_id: Optional organization ID for user-specific keys

        Returns:
            Dict with cost data if found, None otherwise
        """
        try:
            query = db.query(ApiCostMonthly).filter(
                ApiCostMonthly.provider == provider,
                ApiCostMonthly.year == year,
                ApiCostMonthly.month == month,
            )

            if organization_id:
                query = query.filter(ApiCostMonthly.organization_id == organization_id)
            else:
                query = query.filter(ApiCostMonthly.organization_id.is_(None))

            result = query.first()

            if result:
                logger.debug(
                    "Cached costs retrieved",
                    provider=provider,
                    year=year,
                    month=month,
                    is_finalized=result.is_finalized,
                )
                # Use transformer for business logic (DB model → dict)
                return ApiCostTransformer.transform_to_dict(result)

            logger.debug("No cached costs found", provider=provider, year=year, month=month)
            return None

        except SQLAlchemyError as e:
            logger.error(
                "Error retrieving cached costs",
                provider=provider,
                year=year,
                month=month,
                error=str(e),
                error_type=type(e).__name__,
            )
            return None

    def save_month_costs(
        self,
        db: Session,
        provider: str,
        year: int,
        month: int,
        costs: dict[str, Any],
        is_finalized: bool = False,
        organization_id: str | None = None,
    ) -> bool:
        """
        Save or update costs for specific month

        Args:
            db: Database session
            provider: 'openai' or 'mureka'
            year: Year (e.g., 2025)
            month: Month (1-12)
            costs: Dict with total, image, chat, breakdown, etc.
            is_finalized: TRUE = past month (never reload), FALSE = current month (reload with TTL)
            organization_id: Optional organization ID for user-specific keys

        Returns:
            True if successful, False otherwise
        """
        try:
            # Apply defaults using transformer (business logic)
            costs_with_defaults = ApiCostTransformer.apply_cost_defaults(costs)

            # Check if exists (CRUD)
            query = db.query(ApiCostMonthly).filter(
                ApiCostMonthly.provider == provider,
                ApiCostMonthly.year == year,
                ApiCostMonthly.month == month,
            )

            if organization_id:
                query = query.filter(ApiCostMonthly.organization_id == organization_id)
            else:
                query = query.filter(ApiCostMonthly.organization_id.is_(None))

            existing = query.first()

            if existing:
                # Update existing record (CRUD)
                existing.total_cost = costs_with_defaults["total"]
                existing.image_cost = costs_with_defaults["image"]
                existing.chat_cost = costs_with_defaults["chat"]
                existing.currency = costs_with_defaults["currency"]
                existing.line_items = costs_with_defaults["breakdown"]
                existing.bucket_count = costs_with_defaults["bucket_count"]
                existing.is_finalized = is_finalized
                existing.last_updated_at = datetime.now(UTC)
                # Update organization_id if provided
                if organization_id:
                    existing.organization_id = organization_id

                logger.debug(
                    "Updated cached costs",
                    provider=provider,
                    year=year,
                    month=month,
                    total=costs_with_defaults["total"],
                    is_finalized=is_finalized,
                )
            else:
                # Create new record (CRUD)
                new_cost = ApiCostMonthly(
                    provider=provider,
                    organization_id=organization_id,
                    year=year,
                    month=month,
                    total_cost=costs_with_defaults["total"],
                    image_cost=costs_with_defaults["image"],
                    chat_cost=costs_with_defaults["chat"],
                    currency=costs_with_defaults["currency"],
                    line_items=costs_with_defaults["breakdown"],
                    bucket_count=costs_with_defaults["bucket_count"],
                    is_finalized=is_finalized,
                    last_updated_at=datetime.now(UTC),
                )
                db.add(new_cost)

                logger.debug(
                    "Saved cached costs",
                    provider=provider,
                    year=year,
                    month=month,
                    total=costs_with_defaults["total"],
                    is_finalized=is_finalized,
                )

            db.commit()
            return True

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(
                "Error saving costs",
                provider=provider,
                year=year,
                month=month,
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

    def get_all_time_totals(self, db: Session, provider: str) -> tuple[float, float, float]:
        """
        Get sum of all costs across all months (pure DB aggregation)

        Note: Sums ALL entries for the provider, regardless of organization_id.
        This is correct because there's typically only one organization per provider.

        Args:
            db: Database session
            provider: 'openai' or 'mureka'

        Returns:
            Tuple of (total_cost, image_cost, chat_cost) as floats
        """
        try:
            from sqlalchemy import func

            query = db.query(
                func.sum(ApiCostMonthly.total_cost).label("total"),
                func.sum(ApiCostMonthly.image_cost).label("image"),
                func.sum(ApiCostMonthly.chat_cost).label("chat"),
            ).filter(ApiCostMonthly.provider == provider)

            # No organization_id filter - sum ALL entries for this provider
            result = query.first()

            if result and result.total is not None:
                logger.debug(
                    "All-time costs retrieved",
                    provider=provider,
                    total=float(result.total),
                    image=float(result.image or 0),
                    chat=float(result.chat or 0),
                )
                return (
                    float(result.total or 0),
                    float(result.image or 0),
                    float(result.chat or 0),
                )

            logger.debug("No all-time costs found", provider=provider)
            return (0.0, 0.0, 0.0)

        except SQLAlchemyError as e:
            logger.error(
                "Error retrieving all-time costs",
                provider=provider,
                error=str(e),
                error_type=type(e).__name__,
            )
            return (0.0, 0.0, 0.0)
