"""add_stem_url_and_generated_at_to_song_choices

Revision ID: 91c1fff66986
Revises: 0a063377da81
Create Date: 2025-09-25 08:59:23.393478

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "91c1fff66986"
down_revision: str | Sequence[str] | None = "0a063377da81"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - add stem_url and stem_generated_at to song_choices."""
    # Add stem URL columns to song_choices table
    op.add_column("song_choices", sa.Column("stem_url", sa.String(1000), nullable=True))
    op.add_column("song_choices", sa.Column("stem_generated_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema - remove stem_url and stem_generated_at from song_choices."""
    # Remove stem URL columns from song_choices table
    op.drop_column("song_choices", "stem_generated_at")
    op.drop_column("song_choices", "stem_url")
