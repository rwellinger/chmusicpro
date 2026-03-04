"""Unit tests for api_key_middleware - load_user_api_keys and require_api_key"""

from unittest.mock import MagicMock, patch

import pytest
from flask import Flask, g


class TestLoadUserApiKeys:
    @pytest.fixture
    def app(self):
        return Flask(__name__)

    @patch("api.api_key_middleware.user_api_key_orchestrator")
    @patch("api.api_key_middleware.SessionLocal")
    @patch("api.api_key_middleware.get_current_user_id", return_value="user-123")
    def test_loads_keys_into_flask_g(self, mock_get_user, mock_session, mock_orchestrator, app):
        mock_db = MagicMock()
        mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_session.return_value.__exit__ = MagicMock(return_value=False)
        mock_orchestrator.get_decrypted_keys.return_value = {
            "openai_api_key": "sk-openai-123",
            "openai_admin_api_key": "sk-admin-456",
            "claude_api_key": "sk-claude-789",
        }

        with app.test_request_context():
            from api.api_key_middleware import load_user_api_keys

            load_user_api_keys()

            assert g.user_openai_api_key == "sk-openai-123"
            assert g.user_openai_admin_api_key == "sk-admin-456"
            assert g.user_claude_api_key == "sk-claude-789"

        mock_orchestrator.get_decrypted_keys.assert_called_once_with(mock_db, "user-123")

    @patch("api.api_key_middleware.get_current_user_id", return_value=None)
    def test_skips_when_no_user_id(self, mock_get_user, app):
        with app.test_request_context():
            from api.api_key_middleware import load_user_api_keys

            load_user_api_keys()

            assert not hasattr(g, "user_openai_api_key")

    @patch("api.api_key_middleware.user_api_key_orchestrator")
    @patch("api.api_key_middleware.SessionLocal")
    @patch("api.api_key_middleware.get_current_user_id", return_value="user-123")
    def test_sets_none_on_exception(self, mock_get_user, mock_session, mock_orchestrator, app):
        mock_session.return_value.__enter__ = MagicMock(side_effect=Exception("DB down"))
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        with app.test_request_context():
            from api.api_key_middleware import load_user_api_keys

            load_user_api_keys()

            assert g.user_openai_api_key is None
            assert g.user_openai_admin_api_key is None
            assert g.user_claude_api_key is None

    @patch("api.api_key_middleware.user_api_key_orchestrator")
    @patch("api.api_key_middleware.SessionLocal")
    @patch("api.api_key_middleware.get_current_user_id", return_value="user-123")
    def test_handles_partial_keys(self, mock_get_user, mock_session, mock_orchestrator, app):
        mock_db = MagicMock()
        mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_session.return_value.__exit__ = MagicMock(return_value=False)
        mock_orchestrator.get_decrypted_keys.return_value = {
            "openai_api_key": "sk-openai-only",
        }

        with app.test_request_context():
            from api.api_key_middleware import load_user_api_keys

            load_user_api_keys()

            assert g.user_openai_api_key == "sk-openai-only"
            assert g.user_openai_admin_api_key is None
            assert g.user_claude_api_key is None


class TestRequireApiKey:
    @pytest.fixture
    def app(self):
        return Flask(__name__)

    def test_returns_none_when_openai_key_present(self, app):
        with app.test_request_context():
            g.user_openai_api_key = "sk-test"
            from api.api_key_middleware import require_api_key

            assert require_api_key("openai") is None

    def test_returns_none_when_claude_key_present(self, app):
        with app.test_request_context():
            g.user_claude_api_key = "sk-claude"
            from api.api_key_middleware import require_api_key

            assert require_api_key("claude") is None

    def test_returns_none_when_openai_admin_key_present(self, app):
        with app.test_request_context():
            g.user_openai_admin_api_key = "sk-admin"
            from api.api_key_middleware import require_api_key

            assert require_api_key("openai_admin") is None

    def test_returns_error_when_openai_key_missing(self, app):
        with app.test_request_context():
            from api.api_key_middleware import require_api_key

            result = require_api_key("openai")

            assert result is not None
            error_dict, status_code = result
            assert status_code == 403
            assert error_dict["error_code"] == "missing_api_key"
            assert error_dict["provider"] == "openai"
            assert "OpenAI" in error_dict["error"]

    def test_returns_error_when_claude_key_missing(self, app):
        with app.test_request_context():
            from api.api_key_middleware import require_api_key

            result = require_api_key("claude")

            assert result is not None
            error_dict, status_code = result
            assert status_code == 403
            assert error_dict["provider"] == "claude"
            assert "Claude" in error_dict["error"]

    def test_returns_error_for_unknown_provider(self, app):
        with app.test_request_context():
            from api.api_key_middleware import require_api_key

            result = require_api_key("unknown_provider")

            assert result is not None
            error_dict, status_code = result
            assert status_code == 403
            assert error_dict["provider"] == "unknown_provider"

    def test_returns_error_when_key_is_none(self, app):
        with app.test_request_context():
            g.user_openai_api_key = None
            from api.api_key_middleware import require_api_key

            result = require_api_key("openai")

            assert result is not None
            _, status_code = result
            assert status_code == 403

    def test_returns_error_when_key_is_empty_string(self, app):
        with app.test_request_context():
            g.user_openai_api_key = ""
            from api.api_key_middleware import require_api_key

            result = require_api_key("openai")

            assert result is not None
            _, status_code = result
            assert status_code == 403
