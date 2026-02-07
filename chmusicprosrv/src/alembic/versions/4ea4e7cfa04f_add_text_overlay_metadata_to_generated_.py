"""add_text_overlay_metadata_to_generated_images

Revision ID: 4ea4e7cfa04f
Revises: ea8c065212fa
Create Date: 2025-10-23 10:10:53.081260

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "4ea4e7cfa04f"
down_revision: str | Sequence[str] | None = "ea8c065212fa"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add text_overlay_metadata column to generated_images table
    op.add_column(
        "generated_images",
        sa.Column("text_overlay_metadata", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove text_overlay_metadata column
    op.drop_column("generated_images", "text_overlay_metadata")
