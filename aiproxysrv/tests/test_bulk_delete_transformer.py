"""Tests for BulkDeleteTransformer - Business logic unit tests"""

from business.bulk_delete_transformer import BulkDeleteTransformer, DeleteResult


class TestAggregateResults:
    """Test aggregate_results() - categorizes delete results"""

    def test_aggregate_all_deleted(self):
        """All items successfully deleted"""
        results = [
            DeleteResult("id1", "deleted"),
            DeleteResult("id2", "deleted"),
            DeleteResult("id3", "deleted"),
        ]

        aggregated = BulkDeleteTransformer.aggregate_results(results)

        assert aggregated["deleted"] == ["id1", "id2", "id3"]
        assert aggregated["not_found"] == []
        assert aggregated["errors"] == []

    def test_aggregate_all_not_found(self):
        """All items not found"""
        results = [
            DeleteResult("id1", "not_found"),
            DeleteResult("id2", "not_found"),
        ]

        aggregated = BulkDeleteTransformer.aggregate_results(results)

        assert aggregated["deleted"] == []
        assert aggregated["not_found"] == ["id1", "id2"]
        assert aggregated["errors"] == []

    def test_aggregate_all_errors(self):
        """All items errored"""
        results = [
            DeleteResult("id1", "error", "Connection timeout"),
            DeleteResult("id2", "error", "Database locked"),
        ]

        aggregated = BulkDeleteTransformer.aggregate_results(results)

        assert aggregated["deleted"] == []
        assert aggregated["not_found"] == []
        assert aggregated["errors"] == [
            {"id": "id1", "error": "Connection timeout"},
            {"id": "id2", "error": "Database locked"},
        ]

    def test_aggregate_mixed_results(self):
        """Mix of deleted, not found, and errors"""
        results = [
            DeleteResult("id1", "deleted"),
            DeleteResult("id2", "not_found"),
            DeleteResult("id3", "error", "Permission denied"),
            DeleteResult("id4", "deleted"),
        ]

        aggregated = BulkDeleteTransformer.aggregate_results(results)

        assert aggregated["deleted"] == ["id1", "id4"]
        assert aggregated["not_found"] == ["id2"]
        assert aggregated["errors"] == [{"id": "id3", "error": "Permission denied"}]

    def test_aggregate_empty_list(self):
        """Empty results list"""
        results = []

        aggregated = BulkDeleteTransformer.aggregate_results(results)

        assert aggregated["deleted"] == []
        assert aggregated["not_found"] == []
        assert aggregated["errors"] == []

    def test_aggregate_error_without_message(self):
        """Error result without error message (uses default)"""
        results = [DeleteResult("id1", "error", None)]

        aggregated = BulkDeleteTransformer.aggregate_results(results)

        assert aggregated["errors"] == [{"id": "id1", "error": "Unknown error"}]


class TestCreateSummary:
    """Test create_summary() - summary statistics"""

    def test_summary_all_deleted(self):
        """Summary when all items deleted"""
        aggregated = {"deleted": ["id1", "id2", "id3"], "not_found": [], "errors": []}

        summary = BulkDeleteTransformer.create_summary(aggregated, total_requested=3)

        assert summary == {"total_requested": 3, "deleted": 3, "not_found": 0, "errors": 0}

    def test_summary_mixed_results(self):
        """Summary with mixed results"""
        aggregated = {
            "deleted": ["id1", "id2"],
            "not_found": ["id3"],
            "errors": [{"id": "id4", "error": "Failed"}],
        }

        summary = BulkDeleteTransformer.create_summary(aggregated, total_requested=4)

        assert summary == {"total_requested": 4, "deleted": 2, "not_found": 1, "errors": 1}

    def test_summary_empty_results(self):
        """Summary with no results"""
        aggregated = {"deleted": [], "not_found": [], "errors": []}

        summary = BulkDeleteTransformer.create_summary(aggregated, total_requested=0)

        assert summary == {"total_requested": 0, "deleted": 0, "not_found": 0, "errors": 0}

    def test_summary_missing_keys(self):
        """Summary handles missing keys gracefully"""
        aggregated = {}  # Missing all keys

        summary = BulkDeleteTransformer.create_summary(aggregated, total_requested=5)

        assert summary == {"total_requested": 5, "deleted": 0, "not_found": 0, "errors": 0}


class TestFormatBulkDeleteResponse:
    """Test format_bulk_delete_response() - complete response formatting"""

    def test_format_complete_response(self):
        """Format complete response with summary and results"""
        aggregated = {
            "deleted": ["id1", "id2"],
            "not_found": ["id3"],
            "errors": [{"id": "id4", "error": "Failed"}],
        }

        response = BulkDeleteTransformer.format_bulk_delete_response(aggregated, total_requested=4)

        assert response == {
            "summary": {"total_requested": 4, "deleted": 2, "not_found": 1, "errors": 1},
            "results": {
                "deleted": ["id1", "id2"],
                "not_found": ["id3"],
                "errors": [{"id": "id4", "error": "Failed"}],
            },
        }

    def test_format_empty_response(self):
        """Format response with no results"""
        aggregated = {"deleted": [], "not_found": [], "errors": []}

        response = BulkDeleteTransformer.format_bulk_delete_response(aggregated, total_requested=0)

        assert response == {
            "summary": {"total_requested": 0, "deleted": 0, "not_found": 0, "errors": 0},
            "results": {"deleted": [], "not_found": [], "errors": []},
        }


class TestDeleteResult:
    """Test DeleteResult class"""

    def test_create_deleted_result(self):
        """Create successful delete result"""
        result = DeleteResult("id1", "deleted")

        assert result.item_id == "id1"
        assert result.status == "deleted"
        assert result.error_message is None

    def test_create_not_found_result(self):
        """Create not found result"""
        result = DeleteResult("id2", "not_found")

        assert result.item_id == "id2"
        assert result.status == "not_found"
        assert result.error_message is None

    def test_create_error_result(self):
        """Create error result with message"""
        result = DeleteResult("id3", "error", "Database connection failed")

        assert result.item_id == "id3"
        assert result.status == "error"
        assert result.error_message == "Database connection failed"
