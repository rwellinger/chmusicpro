"""add_workflow_field_to_songs

Revision ID: df73746c9254
Revises: ce70bed82146
Create Date: 2025-09-21 13:47:53.637287

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "df73746c9254"
down_revision: str | Sequence[str] | None = "ce70bed82146"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add workflow field to songs table
    op.add_column("songs", sa.Column("workflow", sa.String(length=50), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove workflow field from songs table
    op.drop_column("songs", "workflow")
