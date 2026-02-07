"""Unit tests for LyricParsingRuleController

Note: Success cases with Pydantic model_validate() are tested via integration tests.
These unit tests focus on error handling and edge cases.
"""

from unittest.mock import MagicMock

import pytest

from api.controllers.lyric_parsing_rule_controller import LyricParsingRuleController
from schemas.lyric_parsing_rule_schemas import LyricParsingRuleReorderRequest, LyricParsingRuleUpdate


@pytest.mark.unit
class TestLyricParsingRuleControllerUpdate:
    """Test LyricParsingRuleController.update_rule method"""

    def test_update_rule_not_found(self, mock_db_session):
        """Test update of non-existent rule"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        update_data = LyricParsingRuleUpdate(name="New Name")

        result, status_code = LyricParsingRuleController.update_rule(mock_db_session, 999, update_data)

        assert status_code == 404
        assert "error" in result


@pytest.mark.unit
class TestLyricParsingRuleControllerDelete:
    """Test LyricParsingRuleController.delete_rule method"""

    def test_delete_rule_success(self, mock_db_session):
        """Test successful rule deletion"""
        mock_rule = MagicMock()
        mock_rule.id = 1

        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_rule

        result, status_code = LyricParsingRuleController.delete_rule(mock_db_session, 1)

        assert status_code == 200
        assert "message" in result
        mock_db_session.delete.assert_called_once_with(mock_rule)
        mock_db_session.commit.assert_called_once()

    def test_delete_rule_not_found(self, mock_db_session):
        """Test deletion of non-existent rule"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        result, status_code = LyricParsingRuleController.delete_rule(mock_db_session, 999)

        assert status_code == 404
        assert "error" in result


@pytest.mark.unit
class TestLyricParsingRuleControllerReorder:
    """Test LyricParsingRuleController.reorder_rules method"""

    def test_reorder_rules_missing_ids(self, mock_db_session):
        """Test reordering with non-existent rule IDs"""
        mock_rules = [MagicMock(id=1), MagicMock(id=2)]

        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_rules

        reorder_data = LyricParsingRuleReorderRequest(rule_ids=[1, 2, 999])

        result, status_code = LyricParsingRuleController.reorder_rules(mock_db_session, reorder_data)

        assert status_code == 404
        assert "error" in result
        assert "999" in str(result["error"])
