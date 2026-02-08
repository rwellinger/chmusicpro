"""Unit tests for auth_middleware - admin_required decorator and helpers"""

from unittest.mock import MagicMock, patch

import pytest
from flask import Flask, g, jsonify


class TestAdminRequired:
    """Test suite for admin_required decorator"""

    @pytest.fixture
    def app(self):
        """Create Flask test app with routes using admin_required"""
        app = Flask(__name__)
        app.config["TESTING"] = True

        from api.auth_middleware import admin_required

        @app.route("/admin-only")
        @admin_required
        def admin_route():
            return jsonify({"success": True}), 200

        return app

    def test_admin_required_allows_admin(self, app):
        """Test that admin role passes admin_required check"""
        with app.test_request_context("/admin-only"):
            g.current_user_role = "admin"

            from api.auth_middleware import admin_required

            @admin_required
            def test_func():
                return jsonify({"success": True}), 200

            response, status_code = test_func()
            assert status_code == 200

    def test_admin_required_rejects_user(self, app):
        """Test that regular user role is rejected"""
        with app.test_request_context("/admin-only"):
            g.current_user_role = "user"

            from api.auth_middleware import admin_required

            @admin_required
            def test_func():
                return jsonify({"success": True}), 200

            response, status_code = test_func()
            assert status_code == 403
            data = response.get_json()
            assert data["success"] is False
            assert data["error"] == "Admin access required"

    def test_admin_required_rejects_missing_role(self, app):
        """Test that missing role attribute is rejected"""
        with app.test_request_context("/admin-only"):
            # Don't set g.current_user_role at all

            from api.auth_middleware import admin_required

            @admin_required
            def test_func():
                return jsonify({"success": True}), 200

            response, status_code = test_func()
            assert status_code == 403


class TestGetCurrentUserRole:
    """Test suite for get_current_user_role helper"""

    @pytest.fixture
    def app(self):
        return Flask(__name__)

    def test_returns_role_when_set(self, app):
        """Test that role is returned from g object"""
        with app.test_request_context():
            g.current_user_role = "admin"

            from api.auth_middleware import get_current_user_role

            assert get_current_user_role() == "admin"

    def test_returns_none_when_not_set(self, app):
        """Test that None is returned when role is not set"""
        with app.test_request_context():
            from api.auth_middleware import get_current_user_role

            assert get_current_user_role() is None


class TestJwtRequiredSetsRole:
    """Test that jwt_required sets g.current_user_role"""

    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        return app

    def test_jwt_required_sets_role_on_g(self, app):
        """Test that jwt_required populates g.current_user_role from user model"""
        with app.test_request_context(
            "/test",
            headers={"Authorization": "Bearer valid-token"},
        ):
            mock_user = MagicMock()
            mock_user.role = "admin"

            mock_auth_service = MagicMock()
            mock_auth_service.verify_jwt_token.return_value = {
                "user_id": "test-id",
                "email": "test@test.com",
            }

            mock_user_service = MagicMock()
            mock_user_service.get_user_by_id.return_value = mock_user

            mock_db = MagicMock()

            with (
                patch("api.auth_middleware.UserAuthService", return_value=mock_auth_service),
                patch("api.auth_middleware.UserService", return_value=mock_user_service),
                patch("db.database.get_db", return_value=iter([mock_db])),
            ):
                from api.auth_middleware import jwt_required

                @jwt_required
                def test_func():
                    return g.current_user_role

                result = test_func()
                assert result == "admin"
