"""add_prompt_templates_table

Revision ID: 78f60c60052e
Revises: df73746c9254
Create Date: 2025-09-22 19:31:21.046248

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "78f60c60052e"
down_revision: str | Sequence[str] | None = "df73746c9254"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "prompt_templates",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("pre_condition", sa.Text, nullable=False),
        sa.Column("post_condition", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("version", sa.String(10), nullable=True),
        sa.Column("model_hint", sa.String(50), nullable=True),
        sa.Column("active", sa.Boolean, default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.UniqueConstraint("category", "action", name="uq_prompt_category_action"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("prompt_templates")
