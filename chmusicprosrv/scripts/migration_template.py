"""Migration Template for Idempotent Database Changes

This template demonstrates best practices for writing reliable Alembic migrations:
- Idempotent operations (can run multiple times safely)
- Pre-flight checks before destructive operations
- Clear error messages
- Proper rollback support

Usage:
    1. Copy this file to src/alembic/versions/
    2. Rename with Alembic naming: <revision>_<description>.py
    3. Update revision IDs
    4. Replace placeholder operations with your changes
    5. Test on development first!

Example:
    cp scripts/migration_template.py src/alembic/versions/abc123_add_new_feature.py
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


# revision identifiers, used by Alembic
revision: str = "REPLACE_WITH_NEW_REVISION_ID"
down_revision: str | Sequence[str] | None = "REPLACE_WITH_PARENT_REVISION_ID"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def table_exists(table_name: str) -> bool:
    """Check if table exists in database."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if column exists in table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def index_exists(index_name: str) -> bool:
    """Check if index exists."""
    bind = op.get_bind()
    # Query pg_indexes to check if index exists
    result = bind.execute(sa.text("SELECT indexname FROM pg_indexes WHERE indexname = :name"), {"name": index_name})
    return result.first() is not None


def upgrade() -> None:
    """Upgrade schema - Add your changes here."""

    # ================================================================
    # Example 1: Create table (idempotent)
    # ================================================================
    if not table_exists("example_table"):
        op.create_table(
            "example_table",
            sa.Column(
                "id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
            ),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        )
        print("✅ Created table: example_table")
    else:
        print("ℹ️  Table 'example_table' already exists, skipping creation")

    # ================================================================
    # Example 2: Add column (idempotent)
    # ================================================================
    if table_exists("existing_table") and not column_exists("existing_table", "new_column"):
        op.add_column("existing_table", sa.Column("new_column", sa.String(100), nullable=True))
        print("✅ Added column: existing_table.new_column")
    else:
        print("ℹ️  Column 'existing_table.new_column' already exists or table missing, skipping")

    # ================================================================
    # Example 3: Create index (idempotent)
    # ================================================================
    if not index_exists("ix_example_table_name"):
        op.create_index("ix_example_table_name", "example_table", ["name"])
        print("✅ Created index: ix_example_table_name")
    else:
        print("ℹ️  Index 'ix_example_table_name' already exists, skipping")

    # ================================================================
    # Example 4: Create foreign key (with pre-flight check)
    # ================================================================
    # Note: PostgreSQL doesn't have native "IF NOT EXISTS" for constraints
    # We check manually and suppress errors
    if table_exists("example_table") and table_exists("parent_table"):
        try:
            op.create_foreign_key("fk_example_table_parent_id", "example_table", "parent_table", ["parent_id"], ["id"])
            print("✅ Created foreign key: fk_example_table_parent_id")
        except sa.exc.ProgrammingError as e:
            if "already exists" in str(e):
                print("ℹ️  Foreign key 'fk_example_table_parent_id' already exists, skipping")
            else:
                raise
    else:
        print("⚠️  Skipping foreign key creation: required tables not found")

    # ================================================================
    # Example 5: Data migration (with safety check)
    # ================================================================
    if table_exists("example_table"):
        # Use execute() for data operations
        bind = op.get_bind()

        # Check if migration already ran (example: check for a sentinel value)
        result = bind.execute(
            sa.text("SELECT COUNT(*) FROM example_table WHERE name = :sentinel"), {"sentinel": "MIGRATION_MARKER"}
        )
        count = result.scalar()

        if count == 0:
            # Safe to run migration
            bind.execute(sa.text("UPDATE example_table SET new_column = 'default_value' WHERE new_column IS NULL"))
            print("✅ Migrated data in example_table")
        else:
            print("ℹ️  Data migration already completed, skipping")

    # ================================================================
    # IMPORTANT: Replace examples above with your actual changes!
    # ================================================================


def downgrade() -> None:
    """Downgrade schema - Reverse your changes here."""

    # WARNING: Only implement if truly reversible!
    # If migration is one-way (e.g., data transformation), raise error instead.

    # Example: Check if safe to downgrade
    if table_exists("example_table"):
        bind = op.get_bind()
        result = bind.execute(sa.text("SELECT COUNT(*) FROM example_table"))
        count = result.scalar()

        if count > 0:
            raise RuntimeError("Cannot downgrade: example_table contains data. Manual intervention required!")

    # Reverse operations (in opposite order of upgrade())
    if index_exists("ix_example_table_name"):
        op.drop_index("ix_example_table_name", "example_table")

    if table_exists("existing_table") and column_exists("existing_table", "new_column"):
        op.drop_column("existing_table", "new_column")

    if table_exists("example_table"):
        op.drop_table("example_table")

    print("✅ Downgrade completed")


# ================================================================
# CHECKLIST before running migration:
# ================================================================
# □ Replaced revision IDs
# □ Removed example code
# □ Added your actual schema changes
# □ Made all operations idempotent (can run multiple times)
# □ Added pre-flight checks for destructive operations
# □ Implemented proper downgrade() or raised error if not reversible
# □ Tested on development database first
# □ Verified schema with: python scripts/verify_schema.py
# □ Reviewed diff with: alembic history
# ================================================================
