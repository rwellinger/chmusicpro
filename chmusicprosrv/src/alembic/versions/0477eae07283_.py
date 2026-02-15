"""add system_context_templates table

Revision ID: 0477eae07283
Revises: h8i9j0k1l2m3
Create Date: 2026-02-15 19:26:31.513030

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0477eae07283"
down_revision: str | Sequence[str] | None = "h8i9j0k1l2m3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "system_context_templates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("domain_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["domain_id"], ["domains.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain_id", "name", name="uq_sct_domain_name"),
    )
    op.create_index(
        op.f("ix_system_context_templates_domain_id"), "system_context_templates", ["domain_id"], unique=False
    )
    op.create_index(op.f("ix_system_context_templates_id"), "system_context_templates", ["id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_system_context_templates_id"), table_name="system_context_templates")
    op.drop_index(op.f("ix_system_context_templates_domain_id"), table_name="system_context_templates")
    op.drop_table("system_context_templates")
