"""add_release_description_fields_to_sketches

Revision ID: b58281de7dda
Revises: 4ea4e7cfa04f
Create Date: 2025-10-24 08:33:59.208414

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b58281de7dda"
down_revision: str | Sequence[str] | None = "4ea4e7cfa04f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new release description fields to song_sketches table
    op.add_column("song_sketches", sa.Column("description_long", sa.Text(), nullable=True))
    op.add_column("song_sketches", sa.Column("description_short", sa.String(length=150), nullable=True))
    op.add_column("song_sketches", sa.Column("description_tags", sa.String(length=1000), nullable=True))
    op.add_column("song_sketches", sa.Column("info", sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove release description fields from song_sketches table
    op.drop_column("song_sketches", "info")
    op.drop_column("song_sketches", "description_tags")
    op.drop_column("song_sketches", "description_short")
    op.drop_column("song_sketches", "description_long")
