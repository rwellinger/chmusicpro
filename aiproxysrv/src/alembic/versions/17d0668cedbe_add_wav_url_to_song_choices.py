"""add_wav_url_to_song_choices

Revision ID: 17d0668cedbe
Revises: e88679a23487
Create Date: 2025-12-09 19:45:09.133795

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "17d0668cedbe"
down_revision: str | Sequence[str] | None = "e88679a23487"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("song_choices", sa.Column("wav_url", sa.String(1000), nullable=True))
    op.add_column("song_choices", sa.Column("wav_s3_key", sa.String(500), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("song_choices", "wav_s3_key")
    op.drop_column("song_choices", "wav_url")
