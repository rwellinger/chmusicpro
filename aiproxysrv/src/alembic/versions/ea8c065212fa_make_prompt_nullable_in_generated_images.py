"""make_prompt_nullable_in_generated_images

Revision ID: ea8c065212fa
Revises: bdc6d08baab1
Create Date: 2025-10-22 15:59:54.503497

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "ea8c065212fa"
down_revision: str | Sequence[str] | None = "bdc6d08baab1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Make prompt column nullable in generated_images table.

    This is needed because we now use user_prompt + enhanced_prompt
    instead of the legacy prompt column.
    """
    op.alter_column("generated_images", "prompt", existing_type=sa.Text(), nullable=True)


def downgrade() -> None:
    """Revert prompt column to NOT NULL."""
    # WARNING: This will fail if any rows have NULL prompt values!
    # Only safe to run if all prompts are filled.
    op.alter_column("generated_images", "prompt", existing_type=sa.Text(), nullable=False)
