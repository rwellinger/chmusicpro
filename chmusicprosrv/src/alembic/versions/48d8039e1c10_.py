"""add_s3_keys_to_song_choices

Revision ID: 48d8039e1c10
Revises: eb6cfe73251b
Create Date: 2025-11-14 01:17:16.175131

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "48d8039e1c10"
down_revision: str | Sequence[str] | None = "eb6cfe73251b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - add S3 storage keys to song_choices."""
    # Add S3 key columns to song_choices table for lazy migration pattern
    op.add_column("song_choices", sa.Column("mp3_s3_key", sa.String(500), nullable=True))
    op.add_column("song_choices", sa.Column("flac_s3_key", sa.String(500), nullable=True))
    op.add_column("song_choices", sa.Column("stem_s3_key", sa.String(500), nullable=True))


def downgrade() -> None:
    """Downgrade schema - remove S3 storage keys from song_choices."""
    # Remove S3 key columns from song_choices table
    op.drop_column("song_choices", "stem_s3_key")
    op.drop_column("song_choices", "flac_s3_key")
    op.drop_column("song_choices", "mp3_s3_key")
