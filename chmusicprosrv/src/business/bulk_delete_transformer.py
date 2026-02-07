"""Bulk Delete Transformer - Pure functions for bulk delete operations (testable business logic)"""

from typing import Any


class DeleteResult:
    """Result of a single delete operation"""

    def __init__(
        self,
        item_id: str,
        status: str,  # 'deleted', 'not_found', 'error'
        error_message: str | None = None,
    ):
        self.item_id = item_id
        self.status = status
        self.error_message = error_message


class BulkDeleteTransformer:
    """Transform and aggregate bulk delete results (pure functions, 100% testable)"""

    @staticmethod
    def aggregate_results(results: list[DeleteResult]) -> dict[str, Any]:
        """
        Aggregate individual delete results into categorized lists

        Pure function - no DB, no file system, fully unit-testable

        Args:
            results: List of DeleteResult objects

        Returns:
            Dict with 'deleted', 'not_found', 'errors' lists

        Example:
            results = [
                DeleteResult("id1", "deleted"),
                DeleteResult("id2", "not_found"),
                DeleteResult("id3", "error", "Connection failed")
            ]
            aggregated = BulkDeleteTransformer.aggregate_results(results)
            # {"deleted": ["id1"], "not_found": ["id2"],
            #  "errors": [{"id": "id3", "error": "Connection failed"}]}
        """
        aggregated = {"deleted": [], "not_found": [], "errors": []}

        for result in results:
            if result.status == "deleted":
                aggregated["deleted"].append(result.item_id)
            elif result.status == "not_found":
                aggregated["not_found"].append(result.item_id)
            elif result.status == "error":
                aggregated["errors"].append({"id": result.item_id, "error": result.error_message or "Unknown error"})

        return aggregated

    @staticmethod
    def create_summary(aggregated_results: dict[str, Any], total_requested: int) -> dict[str, int]:
        """
        Create summary statistics from aggregated results

        Pure function - no DB, no file system, fully unit-testable

        Args:
            aggregated_results: Dict with 'deleted', 'not_found', 'errors' lists
            total_requested: Total number of items requested for deletion

        Returns:
            Dict with summary counts

        Example:
            aggregated = {"deleted": ["id1", "id2"], "not_found": ["id3"], "errors": []}
            summary = BulkDeleteTransformer.create_summary(aggregated, 3)
            # {"total_requested": 3, "deleted": 2, "not_found": 1, "errors": 0}
        """
        return {
            "total_requested": total_requested,
            "deleted": len(aggregated_results.get("deleted", [])),
            "not_found": len(aggregated_results.get("not_found", [])),
            "errors": len(aggregated_results.get("errors", [])),
        }

    @staticmethod
    def format_bulk_delete_response(aggregated_results: dict[str, Any], total_requested: int) -> dict[str, Any]:
        """
        Format complete bulk delete response with summary and results

        Pure function - no DB, no file system, fully unit-testable

        Args:
            aggregated_results: Dict with 'deleted', 'not_found', 'errors' lists
            total_requested: Total number of items requested for deletion

        Returns:
            Complete response dict with 'summary' and 'results'

        Example:
            aggregated = {"deleted": ["id1"], "not_found": [], "errors": []}
            response = BulkDeleteTransformer.format_bulk_delete_response(aggregated, 1)
            # {"summary": {"total_requested": 1, "deleted": 1, ...},
            #  "results": {"deleted": ["id1"], ...}}
        """
        summary = BulkDeleteTransformer.create_summary(aggregated_results, total_requested)
        return {"summary": summary, "results": aggregated_results}
