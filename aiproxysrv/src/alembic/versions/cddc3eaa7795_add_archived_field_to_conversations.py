"""add_archived_field_to_conversations

Revision ID: cddc3eaa7795
Revises: 2e4f8b9c3d1a
Create Date: 2025-10-11 16:51:50.310840

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "cddc3eaa7795"
down_revision: str | Sequence[str] | None = "2e4f8b9c3d1a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add archived field to conversations table."""
    # Add archived column with default value false for existing rows
    op.add_column("conversations", sa.Column("archived", sa.Boolean(), nullable=False, server_default="false"))

    # Create composite index for efficient filtering
    op.create_index("ix_conversations_user_archived", "conversations", ["user_id", "archived"])


def downgrade() -> None:
    """Remove archived field from conversations table."""
    # Drop the index first
    op.drop_index("ix_conversations_user_archived", table_name="conversations")

    # Drop the column
    op.drop_column("conversations", "archived")
