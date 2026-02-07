"""
Integration Tests for verify_schema.py

These tests verify that database schema verification works correctly.
They are excluded from coverage reports as they test infrastructure, not business logic.
"""

import contextlib
import sys
from pathlib import Path

import pytest


# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.mark.integration
def test_verify_schema_uses_real_engine():
    """
    REGRESSION TEST: Ensure verify_schema.py uses get_engine() not lazy engine proxy.

    Background:
    - database.py exports 'engine' as _EngineLazy proxy for backwards compatibility
    - SQLAlchemy's inspect() cannot handle proxy objects
    - verify_schema.py must use get_engine() to get real engine instance

    This test prevents regression of the lazy engine bug.
    """
    from unittest.mock import MagicMock, patch

    from scripts.verify_schema import verify_schema
    from sqlalchemy.engine import Engine

    # Mock the inspector to avoid real DB access
    with patch("scripts.verify_schema.inspect") as mock_inspect:
        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = []
        mock_inspect.return_value = mock_inspector

        # This should NOT raise "NoInspectionAvailable" error
        with contextlib.suppress(Exception):
            # Other errors are OK (e.g. no tables), we just check inspect() was called
            verify_schema()

        # Verify inspect() was called with a REAL engine (not lazy proxy)
        assert mock_inspect.called, "inspect() should have been called"
        called_with = mock_inspect.call_args[0][0]

        # Real engine should be SQLAlchemy Engine instance
        assert isinstance(called_with, Engine), f"Expected SQLAlchemy Engine, got {type(called_with).__name__}"


@pytest.mark.integration
def test_verify_schema_imports_get_engine():
    """
    Verify that verify_schema.py imports get_engine() function (not lazy proxy).

    This is a static check that complements the runtime test above.
    """
    from scripts import verify_schema

    # Should have get_engine imported
    assert hasattr(verify_schema, "get_engine"), "verify_schema.py should import get_engine from db.database"

    # Should NOT import 'engine' lazy proxy
    # (This check is defensive - we can't easily detect what was imported)
    # The runtime test above is the real safety net
