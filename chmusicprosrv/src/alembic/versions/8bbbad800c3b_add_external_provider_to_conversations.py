"""add_external_provider_to_conversations

Revision ID: 8bbbad800c3b
Revises: 670a6ec6cf57
Create Date: 2026-01-05 11:33:25.141996

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "8bbbad800c3b"
down_revision: str | Sequence[str] | None = "670a6ec6cf57"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add external_provider column (nullable, since internal provider doesn't need it)
    op.add_column("conversations", sa.Column("external_provider", sa.String(length=50), nullable=True))

    # Data migration: Set external_provider='openai' for existing external conversations
    op.execute(
        """
        UPDATE conversations
        SET external_provider = 'openai'
        WHERE provider = 'external'
        """
    )

    # Create index on external_provider for faster filtering
    op.create_index(op.f("ix_conversations_external_provider"), "conversations", ["external_provider"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index first
    op.drop_index(op.f("ix_conversations_external_provider"), table_name="conversations")

    # Drop column
    op.drop_column("conversations", "external_provider")
