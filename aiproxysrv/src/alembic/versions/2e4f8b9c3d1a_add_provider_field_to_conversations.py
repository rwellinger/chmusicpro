"""Add provider field to conversations table

Revision ID: 2e4f8b9c3d1a
Revises: a0f6d3dc34bf
Create Date: 2025-10-09 15:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "2e4f8b9c3d1a"
down_revision: str | Sequence[str] | None = "a0f6d3dc34bf"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add provider column with default 'internal'
    op.add_column(
        "conversations", sa.Column("provider", sa.String(length=50), nullable=False, server_default="internal")
    )

    # Create index on provider for faster filtering
    op.create_index(op.f("ix_conversations_provider"), "conversations", ["provider"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index first
    op.drop_index(op.f("ix_conversations_provider"), table_name="conversations")

    # Drop column
    op.drop_column("conversations", "provider")
