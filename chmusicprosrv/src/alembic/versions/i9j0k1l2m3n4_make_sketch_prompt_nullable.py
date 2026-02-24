"""Make prompt column nullable in song_sketches

Revision ID: i9j0k1l2m3n4
Revises: c5d6e7f8g9h0
Create Date: 2026-02-24

Music style prompt is no longer required for compositions (moved to Suno Enhancer).
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "i9j0k1l2m3n4"
down_revision = "c5d6e7f8g9h0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("song_sketches", "prompt", nullable=True)


def downgrade() -> None:
    op.execute("UPDATE song_sketches SET prompt = '' WHERE prompt IS NULL")
    op.alter_column("song_sketches", "prompt", nullable=False)
