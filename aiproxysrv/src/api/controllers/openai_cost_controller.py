"""OpenAI Cost Controller - Handles OpenAI Admin API Cost operations"""

import os
import traceback
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

import requests
from dateutil.relativedelta import relativedelta

from config.settings import OPENAI_ADMIN_API_KEY, OPENAI_ADMIN_BASE_URL, OPENAI_ADMIN_TIMEOUT
from db.api_cost_service import ApiCostService
from db.database import SessionLocal
from utils.logger import logger


class OpenAICostController:
    """Controller for OpenAI Admin Cost API integration"""

    CACHE_TTL_SECONDS = int(os.getenv("OPENAI_COST_CACHE_TTL", "3600"))  # Default: 1 hour

    def __init__(self):
        self.api_key = OPENAI_ADMIN_API_KEY
        self.base_url = OPENAI_ADMIN_BASE_URL
        self.timeout = OPENAI_ADMIN_TIMEOUT
        self.cost_service = ApiCostService()

    def fetch_month_costs_raw(self, year: int, month: int, project_ids: list[str] | None = None) -> dict[str, Any]:
        """
        Fetch costs for entire month from OpenAI API (with pagination)

        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)
            project_ids: Optional list of project IDs to filter

        Returns:
            Dict with aggregated costs and breakdown

        Raises:
            OpenAICostAPIError: If API call fails
        """
        if not self.api_key:
            raise OpenAICostAPIError("OPENAI_ADMIN_API_KEY not configured")

        # Calculate Unix timestamps for month range
        start_dt = datetime(year, month, 1, tzinfo=UTC)
        end_dt = start_dt + relativedelta(months=1)
        start_ts = int(start_dt.timestamp())
        end_ts = int(end_dt.timestamp())

        # Build API URL
        api_url = f"{self.base_url}/organization/costs"

        # Build query parameters
        params = {
            "start_time": start_ts,
            "end_time": end_ts,
            "group_by": "line_item",  # Group by service/model (required for Image/Chat breakdown)
            "limit": 31,  # Max days per month (1 bucket = 1 day)
        }
        if project_ids:
            params["project_ids"] = project_ids

        # Set headers with Admin API key
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.debug(
            "Fetching OpenAI costs",
            year=year,
            month=month,
            start_ts=start_ts,
            end_ts=end_ts,
            project_ids=project_ids,
        )

        # Pagination loop
        all_buckets = []
        next_page = None
        organization_id = None

        try:
            while True:
                if next_page:
                    params["page"] = next_page

                response = requests.get(api_url, headers=headers, params=params, timeout=self.timeout)

                # Check for HTTP errors
                if response.status_code != 200:
                    error_body = response.text
                    logger.error(
                        "OpenAI Cost API HTTP Error",
                        status_code=response.status_code,
                        response_body=error_body[:500],
                    )
                    raise OpenAICostAPIError(f"HTTP {response.status_code}: {error_body[:200]}")

                resp_json = response.json()
                all_buckets.extend(resp_json.get("data", []))

                # Extract organization_id from response (top-level or from first result)
                if not organization_id:
                    # Try top-level first
                    organization_id = resp_json.get("organization_id") or resp_json.get("org_id")

                    # If not found, try from first bucket's first result
                    if not organization_id and resp_json.get("data"):
                        logger.debug(
                            "Searching for organization_id in buckets", bucket_count=len(resp_json.get("data", []))
                        )
                        for bucket in resp_json.get("data", []):
                            results = bucket.get("results", [])
                            logger.debug("Checking bucket", result_count=len(results))
                            for result in results:
                                organization_id = result.get("organization_id")
                                logger.debug("Found result", has_org_id=bool(organization_id), org_id=organization_id)
                                if organization_id:
                                    logger.info(
                                        "Organization ID extracted from result", organization_id=organization_id
                                    )
                                    break
                            if organization_id:
                                break

                # Check for more pages
                if not resp_json.get("has_more", False):
                    break

                next_page = resp_json.get("next_page")
                if not next_page:
                    break

            logger.debug("OpenAI costs fetched", year=year, month=month, bucket_count=len(all_buckets))

            # Aggregate line items across all buckets
            line_items = defaultdict(float)
            for bucket in all_buckets:
                for result in bucket.get("results", []):
                    line_item_name = result.get("line_item", "unknown")
                    amount_value = result.get("amount", {}).get("value", 0)

                    # Convert to float if string (defensive handling for API changes)
                    if isinstance(amount_value, str):
                        amount_value = float(amount_value) if amount_value else 0.0

                    line_items[line_item_name] += amount_value

            # Categorize: Image vs Chat
            image_cost = sum(v for k, v in line_items.items() if k.startswith("dall-e"))
            chat_cost = sum(v for k, v in line_items.items() if k.startswith("gpt-"))
            total_cost = sum(line_items.values())

            result = {
                "year": year,
                "month": month,
                "total": total_cost,
                "image": image_cost,
                "chat": chat_cost,
                "currency": "usd",
                "breakdown": dict(line_items),
                "bucket_count": len(all_buckets),
            }

            # Add organization_id if available
            if organization_id:
                result["organization_id"] = organization_id
                logger.debug("Organization ID extracted", organization_id=organization_id)
            else:
                logger.warning("Organization ID not found in API response")

            return result

        except requests.exceptions.RequestException as e:
            logger.error("OpenAI Cost API Network Error", error=str(e), error_type=type(e).__name__)
            raise OpenAICostAPIError(f"Network Error: {e}")
        except Exception as e:
            logger.error(
                "Unexpected OpenAI Cost API error",
                error_type=type(e).__name__,
                error=str(e),
                stacktrace=traceback.format_exc(),
            )
            raise OpenAICostAPIError(f"Unexpected Error: {e}")

    def get_current_month_costs(self) -> tuple[dict[str, Any], int]:
        """
        Get costs for current month (cached with TTL)

        Cache strategy:
        - If cache exists and age < TTL → Return cached
        - If cache expired or not exists → Fetch from API + update cache

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            now = datetime.now(UTC)

            # Check cache - try without organization_id first (for existing entries with org_id)
            with SessionLocal() as db:
                # First try: Find ANY cached entry for this month (ignoring organization_id)
                from db.models import ApiCostMonthly

                cached_record = (
                    db.query(ApiCostMonthly)
                    .filter(
                        ApiCostMonthly.provider == "openai",
                        ApiCostMonthly.year == now.year,
                        ApiCostMonthly.month == now.month,
                    )
                    .first()
                )

                if cached_record:
                    from business.api_cost_transformer import ApiCostTransformer

                    cached = ApiCostTransformer.transform_to_dict(cached_record)

                    if not self._is_cache_expired(cached):
                        ttl_remaining = self._ttl_remaining(cached)
                        logger.debug("Current month costs from cache", ttl_remaining=ttl_remaining)
                        return {"status": "success", "costs": cached, "cached": True}, 200

            # Cache expired or not exists → Fetch from API
            logger.info("Fetching current month costs from OpenAI API")
            costs = self.fetch_month_costs_raw(now.year, now.month)

            # Save/Update cache (is_finalized = False)
            org_id = costs.get("organization_id")
            with SessionLocal() as db:
                self.cost_service.save_month_costs(
                    db, "openai", now.year, now.month, costs, is_finalized=False, organization_id=org_id
                )

            return {"status": "success", "costs": costs, "cached": False}, 200

        except OpenAICostAPIError as e:
            logger.error("OpenAI Cost API error", error=str(e))
            return {"status": "error", "message": str(e)}, 500
        except Exception as e:
            logger.error(
                "Error fetching current month costs",
                error=str(e),
                error_type=type(e).__name__,
                stacktrace=traceback.format_exc(),
            )
            return {"status": "error", "message": f"Unexpected error: {e}"}, 500

    def get_month_costs(self, year: int, month: int) -> tuple[dict[str, Any], int]:
        """
        Get costs for specific month (cached forever if finalized)

        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate: Can't query future months
            now = datetime.now(UTC)
            if year > now.year or (year == now.year and month >= now.month):
                return {
                    "status": "error",
                    "message": "Use /current for current month",
                }, 400

            # Check cache - ignore organization_id for lookup
            with SessionLocal() as db:
                from db.models import ApiCostMonthly

                cached_record = (
                    db.query(ApiCostMonthly)
                    .filter(
                        ApiCostMonthly.provider == "openai",
                        ApiCostMonthly.year == year,
                        ApiCostMonthly.month == month,
                    )
                    .first()
                )

                if cached_record and cached_record.is_finalized:
                    from business.api_cost_transformer import ApiCostTransformer

                    cached = ApiCostTransformer.transform_to_dict(cached_record)
                    logger.debug("Historical month costs from cache (finalized)", year=year, month=month)
                    return {"status": "success", "costs": cached, "cached": True}, 200

            # Not cached or not finalized → Fetch from API
            logger.info("Fetching historical month costs from OpenAI API", year=year, month=month)
            costs = self.fetch_month_costs_raw(year, month)

            # Save cache (is_finalized = True for past months)
            org_id = costs.get("organization_id")
            with SessionLocal() as db:
                self.cost_service.save_month_costs(
                    db, "openai", year, month, costs, is_finalized=True, organization_id=org_id
                )

            return {"status": "success", "costs": costs, "cached": False}, 200

        except OpenAICostAPIError as e:
            logger.error("OpenAI Cost API error", error=str(e))
            return {"status": "error", "message": str(e)}, 500
        except Exception as e:
            logger.error(
                "Error fetching month costs",
                year=year,
                month=month,
                error=str(e),
                error_type=type(e).__name__,
                stacktrace=traceback.format_exc(),
            )
            return {"status": "error", "message": f"Unexpected error: {e}"}, 500

    def get_all_time_costs(self) -> tuple[dict[str, Any], int]:
        """
        Get all-time aggregated costs across all months

        Sums all costs for provider 'openai', regardless of organization_id.

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            with SessionLocal() as db:
                # Get aggregated totals from repository (pure DB operation)
                total, image, chat = self.cost_service.get_all_time_totals(db, "openai")

                # Transform to response format using business layer
                from business.api_cost_transformer import ApiCostTransformer

                costs = ApiCostTransformer.format_all_time_costs(total, image, chat)

                logger.debug("All-time costs calculated", total=total, image=image, chat=chat)

                return {"status": "success", "costs": costs}, 200

        except Exception as e:
            logger.error(
                "Error fetching all-time costs",
                error=str(e),
                error_type=type(e).__name__,
                stacktrace=traceback.format_exc(),
            )
            return {"status": "error", "message": f"Unexpected error: {e}"}, 500

    def _is_cache_expired(self, cached: dict) -> bool:
        """Check if cache is expired (based on TTL)"""
        if cached.get("is_finalized"):
            return False  # Finalized = never expires

        last_updated = cached.get("last_updated_at")
        if not last_updated:
            return True

        age_seconds = (datetime.now(UTC) - last_updated).total_seconds()
        return age_seconds > self.CACHE_TTL_SECONDS

    def _ttl_remaining(self, cached: dict) -> int:
        """Calculate remaining TTL in seconds"""
        last_updated = cached.get("last_updated_at")
        if not last_updated:
            return 0
        age_seconds = (datetime.now(UTC) - last_updated).total_seconds()
        return max(0, int(self.CACHE_TTL_SECONDS - age_seconds))


class OpenAICostAPIError(Exception):
    """Custom exception for OpenAI Cost API errors"""

    pass
