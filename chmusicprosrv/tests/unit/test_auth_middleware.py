"""Unit tests for auth_middleware - decorators and helpers"""

from unittest.mock import MagicMock, patch

import pytest
from flask import Flask, g, jsonify


class TestDomainRoleRequired:
    """Test suite for domain_role_required decorator"""

    @pytest.fixture
    def app(self):
        return Flask(__name__)

    def test_allows_matching_active_domain_role(self, app):
        """Test that matching active domain role is allowed"""
        with app.test_request_context():
            g.current_domain_role = "admin"

            from api.auth_middleware import domain_role_required

            @domain_role_required("admin", "owner")
            def test_func():
                return jsonify({"success": True}), 200

            response, status_code = test_func()
            assert status_code == 200

    def test_rejects_non_matching_active_domain_role(self, app):
        """Test that non-matching active domain role is rejected"""
        with app.test_request_context():
            g.current_domain_role = "viewer"

            from api.auth_middleware import domain_role_required

            @domain_role_required("admin", "owner")
            def test_func():
                return jsonify({"success": True}), 200

            response, status_code = test_func()
            assert status_code == 403
            data = response.get_json()
            assert data["error"] == "Insufficient domain permissions"

    def test_rejects_missing_domain_role(self, app):
        """Test that missing domain role is rejected"""
        with app.test_request_context():
            from api.auth_middleware import domain_role_required

            @domain_role_required("admin", "owner")
            def test_func():
                return jsonify({"success": True}), 200

            response, status_code = test_func()
            assert status_code == 403

    def test_domain_type_allows_matching_role(self, app):
        """Test that domain_type lookup allows matching role"""
        with app.test_request_context():
            g.current_user_id = "test-user-id"

            mock_domain = MagicMock()
            mock_domain.id = "system-domain-id"

            mock_domain_svc = MagicMock()
            mock_domain_svc.get_reserved_domain.return_value = mock_domain
            mock_domain_svc.get_user_role_in_domain.return_value = "admin"

            mock_db = MagicMock()

            from api.auth_middleware import domain_role_required
            from db.models import DomainType

            with (
                patch("db.domain_service.DomainService", return_value=mock_domain_svc),
                patch("db.database.get_db", return_value=iter([mock_db])),
            ):

                @domain_role_required("admin", "owner", domain_type=DomainType.SYSTEM)
                def test_func():
                    return jsonify({"success": True}), 200

                response, status_code = test_func()
                assert status_code == 200

            mock_domain_svc.get_reserved_domain.assert_called_once_with(mock_db, DomainType.SYSTEM)
            mock_domain_svc.get_user_role_in_domain.assert_called_once_with(
                mock_db, str(mock_domain.id), "test-user-id"
            )

    def test_domain_type_rejects_non_matching_role(self, app):
        """Test that domain_type lookup rejects non-matching role"""
        with app.test_request_context():
            g.current_user_id = "test-user-id"

            mock_domain = MagicMock()
            mock_domain.id = "system-domain-id"

            mock_domain_svc = MagicMock()
            mock_domain_svc.get_reserved_domain.return_value = mock_domain
            mock_domain_svc.get_user_role_in_domain.return_value = "viewer"

            mock_db = MagicMock()

            from api.auth_middleware import domain_role_required
            from db.models import DomainType

            with (
                patch("db.domain_service.DomainService", return_value=mock_domain_svc),
                patch("db.database.get_db", return_value=iter([mock_db])),
            ):

                @domain_role_required("admin", "owner", domain_type=DomainType.SYSTEM)
                def test_func():
                    return jsonify({"success": True}), 200

                response, status_code = test_func()
                assert status_code == 403

    def test_domain_type_rejects_non_member(self, app):
        """Test that domain_type lookup rejects user with no membership"""
        with app.test_request_context():
            g.current_user_id = "test-user-id"

            mock_domain = MagicMock()
            mock_domain.id = "system-domain-id"

            mock_domain_svc = MagicMock()
            mock_domain_svc.get_reserved_domain.return_value = mock_domain
            mock_domain_svc.get_user_role_in_domain.return_value = None

            mock_db = MagicMock()

            from api.auth_middleware import domain_role_required
            from db.models import DomainType

            with (
                patch("db.domain_service.DomainService", return_value=mock_domain_svc),
                patch("db.database.get_db", return_value=iter([mock_db])),
            ):

                @domain_role_required("admin", "owner", domain_type=DomainType.SYSTEM)
                def test_func():
                    return jsonify({"success": True}), 200

                response, status_code = test_func()
                assert status_code == 403

    def test_domain_type_rejects_missing_user_id(self, app):
        """Test that domain_type rejects when user_id is missing from g"""
        with app.test_request_context():
            # Don't set g.current_user_id
            from api.auth_middleware import domain_role_required
            from db.models import DomainType

            @domain_role_required("admin", "owner", domain_type=DomainType.SYSTEM)
            def test_func():
                return jsonify({"success": True}), 200

            response, status_code = test_func()
            assert status_code == 403

    def test_domain_type_rejects_missing_domain(self, app):
        """Test that domain_type rejects when reserved domain not found"""
        with app.test_request_context():
            g.current_user_id = "test-user-id"

            mock_domain_svc = MagicMock()
            mock_domain_svc.get_reserved_domain.return_value = None

            mock_db = MagicMock()

            from api.auth_middleware import domain_role_required
            from db.models import DomainType

            with (
                patch("db.domain_service.DomainService", return_value=mock_domain_svc),
                patch("db.database.get_db", return_value=iter([mock_db])),
            ):

                @domain_role_required("admin", "owner", domain_type=DomainType.SYSTEM)
                def test_func():
                    return jsonify({"success": True}), 200

                response, status_code = test_func()
                assert status_code == 403
