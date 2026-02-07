#!/usr/bin/env python3
"""
Database Schema Verification Script

Verifies that the actual database schema matches the expected SQLAlchemy models.
This script runs after Alembic migrations to ensure consistency.

Usage:
    python scripts/verify_schema.py

Exit Codes:
    0 - Schema is consistent
    1 - Schema inconsistencies detected
    2 - Connection error or other failure
"""

import sys
from pathlib import Path


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import inspect

from db.database import get_engine
from db.models import Base


def verify_schema() -> int:
    """
    Verify database schema matches SQLAlchemy models.

    Returns:
        0 if schema is consistent, 1 if inconsistencies found, 2 on error
    """
    try:
        inspector = inspect(get_engine())
        errors = []

        # 1. Check all expected tables exist
        print("🔍 Verifying database schema...")
        print("")

        expected_tables = set(Base.metadata.tables.keys())
        actual_tables = set(inspector.get_table_names(schema="public"))

        missing_tables = expected_tables - actual_tables
        if missing_tables:
            errors.append(f"❌ Missing tables: {', '.join(sorted(missing_tables))}")

        extra_tables = actual_tables - expected_tables - {"alembic_version"}
        if extra_tables:
            print(f"⚠️  Extra tables (not in models): {', '.join(sorted(extra_tables))}")

        # 2. Verify critical columns for key tables
        critical_checks = {
            "songs": [
                ("id", "UUID"),
                ("task_id", "VARCHAR"),
                ("sketch_id", "UUID"),  # Critical: Added in migration d4641a241b98
                ("lyrics", "TEXT"),
                ("prompt", "TEXT"),
                ("status", "VARCHAR"),
            ],
            "song_sketches": [
                ("id", "UUID"),
                ("title", "VARCHAR"),
                ("lyrics", "TEXT"),
                ("prompt", "TEXT"),
                ("workflow", "VARCHAR"),
            ],
            "song_choices": [
                ("id", "UUID"),
                ("song_id", "UUID"),
                ("mp3_url", "VARCHAR"),
                ("flac_url", "VARCHAR"),
            ],
            "conversations": [
                ("id", "UUID"),
                ("user_id", "UUID"),
                ("title", "VARCHAR"),
                ("model", "VARCHAR"),
                ("provider", "VARCHAR"),
                ("system_context", "TEXT"),
            ],
            "messages": [
                ("id", "UUID"),
                ("conversation_id", "UUID"),
                ("role", "VARCHAR"),
                ("content", "TEXT"),
            ],
            "messages_archive": [
                ("id", "UUID"),
                ("original_message_id", "UUID"),
                ("conversation_id", "UUID"),
                ("role", "VARCHAR"),
                ("content", "TEXT"),
            ],
            "lyric_parsing_rules": [
                ("id", "INTEGER"),
                ("pattern", "TEXT"),
                ("replacement", "TEXT"),
                ("rule_type", "VARCHAR"),
                ("active", "BOOLEAN"),
            ],
            "generated_images": [
                ("id", "UUID"),
                ("prompt", "TEXT"),
                ("filename", "VARCHAR"),
                ("file_path", "VARCHAR"),
                ("size", "VARCHAR"),
            ],
            "prompt_templates": [
                ("id", "INTEGER"),
                ("category", "VARCHAR"),
                ("action", "VARCHAR"),
                ("pre_condition", "TEXT"),
                ("post_condition", "TEXT"),
                ("active", "BOOLEAN"),
            ],
            "users": [
                ("id", "UUID"),
                ("email", "VARCHAR"),
                ("is_active", "BOOLEAN"),
            ],
            "api_costs_monthly": [
                ("id", "UUID"),
                ("provider", "VARCHAR"),
                ("year", "INTEGER"),
                ("month", "INTEGER"),
                ("total_cost", "NUMERIC"),
                ("is_finalized", "BOOLEAN"),
            ],
            "equipment": [
                ("id", "UUID"),
                ("type", "VARCHAR"),
                ("name", "VARCHAR"),
                ("version", "VARCHAR"),
                ("status", "VARCHAR"),
                ("user_id", "UUID"),
            ],
        }

        for table_name, expected_columns in critical_checks.items():
            if table_name not in actual_tables:
                continue  # Already reported as missing

            actual_columns = {col["name"]: col for col in inspector.get_columns(table_name, schema="public")}

            for col_name, expected_type_prefix in expected_columns:
                if col_name not in actual_columns:
                    errors.append(f"❌ Table '{table_name}' missing column: {col_name}")
                else:
                    actual_type = str(actual_columns[col_name]["type"]).upper()
                    if not actual_type.startswith(expected_type_prefix):
                        errors.append(
                            f"❌ Table '{table_name}' column '{col_name}' "
                            f"has type {actual_type}, expected {expected_type_prefix}*"
                        )

        # 3. Verify critical foreign keys
        critical_fks = {
            "songs": [("fk_songs_sketch_id", "song_sketches")],
            "song_choices": [("song_choices_song_id_fkey", "songs")],
            "messages": [("messages_conversation_id_fkey", "conversations")],
            "messages_archive": [("messages_archive_conversation_id_fkey", "conversations")],
            "conversations": [("conversations_user_id_fkey", "users")],
            "equipment": [("equipment_user_id_fkey", "users")],
        }

        for table_name, expected_fks in critical_fks.items():
            if table_name not in actual_tables:
                continue

            actual_fks = inspector.get_foreign_keys(table_name, schema="public")
            actual_fk_names = {fk.get("name") for fk in actual_fks if fk.get("name")}

            for fk_name, _referred_table in expected_fks:
                # Check if FK exists (name might vary slightly)
                if not any(fk_name in name for name in actual_fk_names):
                    # Only warn, not error (FK names can vary)
                    print(f"⚠️  Table '{table_name}' might be missing FK: {fk_name}")

        # 4. Report results
        print("")
        if errors:
            print("❌ Schema verification FAILED!")
            print("")
            for error in errors:
                print(f"  {error}")
            print("")
            print(f"Total errors: {len(errors)}")
            return 1
        else:
            print("✅ Schema verification PASSED!")
            print(f"   Tables verified: {len(expected_tables)}")
            print(f"   Critical columns checked: {sum(len(cols) for cols in critical_checks.values())}")
            print("")
            return 0

    except Exception as e:
        print(f"❌ Schema verification ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 2


if __name__ == "__main__":
    exit_code = verify_schema()
    sys.exit(exit_code)
