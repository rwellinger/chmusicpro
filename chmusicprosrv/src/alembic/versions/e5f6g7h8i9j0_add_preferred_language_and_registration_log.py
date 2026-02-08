"""Add preferred_language to users and registration_log table

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2026-02-08

"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op


# revision identifiers, used by Alembic.
revision = "e5f6g7h8i9j0"
down_revision = "d4e5f6g7h8i9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add preferred_language to users table
    op.add_column(
        "users",
        sa.Column("preferred_language", sa.String(5), nullable=False, server_default="en"),
    )

    # Create registration_log table
    op.create_table(
        "registration_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("registered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=True),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("preferred_language", sa.String(5), nullable=False, server_default="en"),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("registration_log")
    op.drop_column("users", "preferred_language")
