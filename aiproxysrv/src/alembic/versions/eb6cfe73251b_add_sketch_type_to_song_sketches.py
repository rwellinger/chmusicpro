"""add_sketch_type_to_song_sketches

Revision ID: eb6cfe73251b
Revises: abe5d41256e3
Create Date: 2025-11-11 18:19:17.855807

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "eb6cfe73251b"
down_revision: str | Sequence[str] | None = "abe5d41256e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - Add sketch_type column to song_sketches."""
    # Add sketch_type column with default 'song' for backwards compatibility
    op.add_column(
        "song_sketches", sa.Column("sketch_type", sa.String(length=20), nullable=False, server_default="song")
    )

    # Add check constraint to ensure only valid types
    op.create_check_constraint("check_sketch_type", "song_sketches", "sketch_type IN ('inspiration', 'song')")


def downgrade() -> None:
    """Downgrade schema - Remove sketch_type column."""
    # Drop check constraint first
    op.drop_constraint("check_sketch_type", "song_sketches", type_="check")

    # Drop column
    op.drop_column("song_sketches", "sketch_type")
