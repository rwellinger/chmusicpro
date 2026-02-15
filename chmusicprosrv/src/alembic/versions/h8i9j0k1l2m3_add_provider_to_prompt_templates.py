"""Add provider column to prompt_templates

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-02-15

Adds provider column to prompt_templates table for multi-provider AI support.
Default 'ollama' preserves existing behavior - no data migration needed.
"""

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision = "h8i9j0k1l2m3"
down_revision = "g7h8i9j0k1l2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "prompt_templates",
        sa.Column("provider", sa.String(50), nullable=False, server_default="ollama"),
    )
    op.create_index("ix_prompt_templates_provider", "prompt_templates", ["provider"])


def downgrade() -> None:
    op.drop_index("ix_prompt_templates_provider", table_name="prompt_templates")
    op.drop_column("prompt_templates", "provider")
