"""add_api_costs_monthly

Revision ID: 0femi2213rz5
Revises: b58281de7dda
Create Date: 2025-10-25 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0femi2213rz5"
down_revision: str | Sequence[str] | None = "b58281de7dda"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create api_costs_monthly table for OpenAI/Mureka cost tracking
    op.create_table(
        "api_costs_monthly",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("organization_id", sa.String(length=100), nullable=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("total_cost", sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column("image_cost", sa.Numeric(precision=12, scale=6), server_default="0"),
        sa.Column("chat_cost", sa.Numeric(precision=12, scale=6), server_default="0"),
        sa.Column("currency", sa.String(length=3), server_default="usd"),
        sa.Column("line_items", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("bucket_count", sa.Integer(), nullable=True),
        sa.Column("project_ids", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("is_finalized", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "last_updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "organization_id", "year", "month", name="uq_provider_org_year_month"),
    )

    # Create indexes
    op.create_index("ix_api_costs_monthly_id", "api_costs_monthly", ["id"])
    op.create_index("ix_api_costs_monthly_provider", "api_costs_monthly", ["provider"])
    op.create_index("ix_api_costs_monthly_organization_id", "api_costs_monthly", ["organization_id"])
    op.create_index("ix_api_costs_monthly_year", "api_costs_monthly", ["year"])
    op.create_index("ix_api_costs_monthly_month", "api_costs_monthly", ["month"])
    op.create_index("ix_api_costs_monthly_is_finalized", "api_costs_monthly", ["is_finalized"])

    # Composite index for common query patterns
    op.create_index(
        "ix_api_costs_monthly_provider_year_month",
        "api_costs_monthly",
        ["provider", "year", "month"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index("ix_api_costs_monthly_provider_year_month", table_name="api_costs_monthly")
    op.drop_index("ix_api_costs_monthly_is_finalized", table_name="api_costs_monthly")
    op.drop_index("ix_api_costs_monthly_month", table_name="api_costs_monthly")
    op.drop_index("ix_api_costs_monthly_year", table_name="api_costs_monthly")
    op.drop_index("ix_api_costs_monthly_organization_id", table_name="api_costs_monthly")
    op.drop_index("ix_api_costs_monthly_provider", table_name="api_costs_monthly")
    op.drop_index("ix_api_costs_monthly_id", table_name="api_costs_monthly")

    # Drop table
    op.drop_table("api_costs_monthly")
