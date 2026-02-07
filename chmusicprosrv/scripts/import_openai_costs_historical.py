#!/usr/bin/env python3
"""Import historical OpenAI costs from Admin API into database

This script fetches historical monthly cost data from OpenAI Admin API
and stores it in the database with is_finalized=True.

Usage:
    # Single month
    python import_openai_costs_historical.py 2025-08

    # Multiple months
    python import_openai_costs_historical.py 2025-08 2025-09 2025-10

    # Dry-run (show data without saving)
    python import_openai_costs_historical.py --dry-run 2025-08

    # With --months flag
    python import_openai_costs_historical.py --months 2025-08 2025-09

Example Output:
    ✓ 2025-08: $4.88 (Chat: $4.88, Image: $0.00)
    ✓ 2025-09: $0.00 (Chat: $0.00, Image: $0.00)
"""

import argparse
import sys
from datetime import UTC, datetime

from api.controllers.openai_cost_controller import OpenAICostAPIError, OpenAICostController
from db.api_cost_service import ApiCostService
from db.database import SessionLocal
from utils.logger import logger


def parse_month(month_str: str) -> tuple[int, int]:
    """
    Parse month string into year and month

    Args:
        month_str: Format 'YYYY-MM' (e.g., '2025-08')

    Returns:
        Tuple of (year, month)

    Raises:
        ValueError: If format is invalid
    """
    try:
        parts = month_str.split("-")
        if len(parts) != 2:
            raise ValueError(f"Invalid format: {month_str}")

        year = int(parts[0])
        month = int(parts[1])

        if not (1 <= month <= 12):
            raise ValueError(f"Month must be 1-12, got: {month}")

        if year < 2020 or year > 2100:
            raise ValueError(f"Year seems invalid: {year}")

        return year, month

    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid month format '{month_str}'. Expected 'YYYY-MM' (e.g., '2025-08')") from e


def validate_historical_month(year: int, month: int) -> None:
    """
    Validate that month is in the past (not current or future)

    Args:
        year: Year
        month: Month (1-12)

    Raises:
        ValueError: If month is current or future
    """
    now = datetime.now(UTC)
    if year > now.year or (year == now.year and month >= now.month):
        raise ValueError(f"Cannot import current/future month {year}-{month:02d}. Use API /current endpoint instead.")


def import_month(
    controller: OpenAICostController,
    cost_service: ApiCostService,
    year: int,
    month: int,
    dry_run: bool = False,
) -> dict:
    """
    Import costs for single month

    Args:
        controller: OpenAICostController instance
        cost_service: ApiCostService instance
        year: Year
        month: Month (1-12)
        dry_run: If True, only fetch data without saving

    Returns:
        Dict with fetched cost data

    Raises:
        OpenAICostAPIError: If API call fails
    """
    logger.info("Fetching costs from OpenAI API", year=year, month=month)

    # Fetch from API (automatically calculates full month: 1st to last day)
    costs = controller.fetch_month_costs_raw(year, month)

    # Extract values
    total = float(costs.get("total", 0))
    chat = float(costs.get("chat", 0))
    image = float(costs.get("image", 0))
    org_id = costs.get("organization_id")

    # Print summary
    if dry_run:
        print(f"[DRY-RUN] {year}-{month:02d}: ${total:.2f} (Chat: ${chat:.2f}, Image: ${image:.2f})")
        if org_id:
            print(f"          Organization ID: {org_id}")
    else:
        print(f"✓ {year}-{month:02d}: ${total:.2f} (Chat: ${chat:.2f}, Image: ${image:.2f})")

    # Save to database (if not dry-run)
    if not dry_run:
        with SessionLocal() as db:
            success = cost_service.save_month_costs(
                db, provider="openai", year=year, month=month, costs=costs, is_finalized=True, organization_id=org_id
            )
            if not success:
                raise RuntimeError(f"Failed to save costs for {year}-{month:02d}")

        logger.info("Costs saved to database", year=year, month=month, is_finalized=True)

    return costs


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Import historical OpenAI costs from Admin API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 2025-08
  %(prog)s 2025-08 2025-09 2025-10
  %(prog)s --dry-run 2025-08
  %(prog)s --months 2025-08 2025-09
        """,
    )

    parser.add_argument("months", nargs="*", help="Months to import in format YYYY-MM (e.g., 2025-08)")
    parser.add_argument("--months", dest="months_flag", nargs="+", help="Alternative: specify months with flag")
    parser.add_argument("--dry-run", action="store_true", help="Fetch data without saving to database")

    args = parser.parse_args()

    # Combine positional and flag arguments
    month_args = args.months or []
    if args.months_flag:
        month_args.extend(args.months_flag)

    if not month_args:
        parser.print_help()
        print("\nError: No months specified")
        sys.exit(1)

    # Parse and validate months
    try:
        months_to_import = []
        for month_str in month_args:
            year, month = parse_month(month_str)
            validate_historical_month(year, month)
            months_to_import.append((year, month))

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Initialize services
    controller = OpenAICostController()
    cost_service = ApiCostService()

    # Print summary
    if args.dry_run:
        print(f"\n[DRY-RUN MODE] Fetching {len(months_to_import)} month(s) from OpenAI API\n")
    else:
        print(f"\nImporting {len(months_to_import)} month(s) from OpenAI API\n")

    # Import each month
    success_count = 0
    error_count = 0

    for year, month in months_to_import:
        try:
            import_month(controller, cost_service, year, month, dry_run=args.dry_run)
            success_count += 1

        except OpenAICostAPIError as e:
            print(f"✗ {year}-{month:02d}: API Error - {e}", file=sys.stderr)
            logger.error("OpenAI API error", year=year, month=month, error=str(e))
            error_count += 1

        except Exception as e:
            print(f"✗ {year}-{month:02d}: Unexpected Error - {e}", file=sys.stderr)
            logger.error("Unexpected error", year=year, month=month, error=str(e), error_type=type(e).__name__)
            error_count += 1

    # Final summary
    print(f"\n{'=' * 60}")
    if args.dry_run:
        print(f"Dry-Run Complete: {success_count} month(s) fetched, {error_count} error(s)")
    else:
        print(f"Import Complete: {success_count} month(s) imported, {error_count} error(s)")

    if error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
