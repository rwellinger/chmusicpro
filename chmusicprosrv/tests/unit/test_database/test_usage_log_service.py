"""Unit tests for UsageLogService"""

from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from db.usage_log_service import UsageLogService


class TestUsageLogService:
    """Test suite for UsageLogService (CRUD operations)"""

    @pytest.fixture
    def service(self):
        return UsageLogService()

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.rollback = MagicMock()
        return db

    def test_create_log_success(self, service, mock_db):
        """Test successful usage log creation"""
        result = service.create_log(
            db=mock_db,
            user_id="123e4567-e89b-12d3-a456-426614174000",
            endpoint="generate-unified",
            model="llama3.2:3b",
            category="lyrics",
            action="generate",
            prompt_tokens=100,
            eval_tokens=200,
            total_duration_ns=5000000000,
        )

        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_log_minimal_params(self, service, mock_db):
        """Test usage log creation with only required params"""
        result = service.create_log(
            db=mock_db,
            user_id="123e4567-e89b-12d3-a456-426614174000",
            endpoint="generate-unified",
            model="llama3.2:3b",
        )

        assert result is not None
        mock_db.add.assert_called_once()

    def test_create_log_db_error(self, service, mock_db):
        """Test that DB errors are handled gracefully"""
        mock_db.commit.side_effect = SQLAlchemyError("DB error")

        result = service.create_log(
            db=mock_db,
            user_id="123e4567-e89b-12d3-a456-426614174000",
            endpoint="generate-unified",
            model="llama3.2:3b",
        )

        assert result is None
        mock_db.rollback.assert_called_once()

    def test_create_log_unexpected_error(self, service, mock_db):
        """Test that unexpected errors are handled gracefully"""
        mock_db.add.side_effect = RuntimeError("Unexpected error")

        result = service.create_log(
            db=mock_db,
            user_id="123e4567-e89b-12d3-a456-426614174000",
            endpoint="generate-unified",
            model="llama3.2:3b",
        )

        assert result is None

    def test_create_log_sets_correct_fields(self, service, mock_db):
        """Test that all fields are set correctly on the model"""
        result = service.create_log(
            db=mock_db,
            user_id="123e4567-e89b-12d3-a456-426614174000",
            endpoint="generate-unified",
            model="gpt-oss:20b",
            category="lyrics",
            action="refine",
            prompt_tokens=50,
            eval_tokens=150,
            total_duration_ns=3000000000,
        )

        assert result is not None
        assert result.user_id == "123e4567-e89b-12d3-a456-426614174000"
        assert result.endpoint == "generate-unified"
        assert result.model == "gpt-oss:20b"
        assert result.category == "lyrics"
        assert result.action == "refine"
        assert result.prompt_tokens == 50
        assert result.eval_tokens == 150
        assert result.total_duration_ns == 3000000000
