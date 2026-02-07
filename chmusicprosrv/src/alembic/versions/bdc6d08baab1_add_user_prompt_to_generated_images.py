"""add_user_prompt_to_generated_images

Revision ID: bdc6d08baab1
Revises: ee8edc060263
Create Date: 2025-10-22 13:52:14.525751

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "bdc6d08baab1"
down_revision: str | Sequence[str] | None = "ee8edc060263"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add user_prompt column to generated_images table
    op.add_column("generated_images", sa.Column("user_prompt", sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove user_prompt column from generated_images table
    op.drop_column("generated_images", "user_prompt")
