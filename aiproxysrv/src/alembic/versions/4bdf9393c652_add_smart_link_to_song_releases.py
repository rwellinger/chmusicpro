"""add_smart_link_to_song_releases

Revision ID: 4bdf9393c652
Revises: 48d8039e1c10
Create Date: 2025-11-21 17:01:54.401020

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "4bdf9393c652"
down_revision: str | Sequence[str] | None = "48d8039e1c10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("song_releases", sa.Column("smart_link", sa.String(1000), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("song_releases", "smart_link")
