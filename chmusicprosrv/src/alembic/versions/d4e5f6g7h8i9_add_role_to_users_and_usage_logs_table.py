"""Add role to users and create usage_logs table

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-02-08

Multi-Tenancy Phase 2: Add role column to users table for RBAC,
create usage_logs table for per-user AI usage tracking.
"""

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID

from alembic import op


# revision identifiers, used by Alembic.
revision = "d4e5f6g7h8i9"
down_revision = "c3d4e5f6g7h8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Add role column to users table (with server_default for backfill)
    op.add_column("users", sa.Column("role", sa.String(20), nullable=False, server_default="user"))

    # Step 2: Backfill all existing users to "user" role (server_default handles this)
    # Then set first active user to "admin"
    connection = op.get_bind()
    first_user = connection.execute(
        text("SELECT id FROM users WHERE is_active = true ORDER BY created_at ASC LIMIT 1")
    ).fetchone()

    if first_user:
        connection.execute(
            text("UPDATE users SET role = 'admin' WHERE id = :user_id"),
            {"user_id": str(first_user[0])},
        )

    # Step 3: Create usage_logs table
    op.create_table(
        "usage_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("endpoint", sa.String(100), nullable=False),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("action", sa.String(50), nullable=True),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("prompt_tokens", sa.Integer, nullable=True),
        sa.Column("eval_tokens", sa.Integer, nullable=True),
        sa.Column("total_duration_ns", sa.BigInteger, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_usage_logs_id", "usage_logs", ["id"])
    op.create_index("ix_usage_logs_user_id", "usage_logs", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_usage_logs_user_id", table_name="usage_logs")
    op.drop_index("ix_usage_logs_id", table_name="usage_logs")
    op.drop_table("usage_logs")
    op.drop_column("users", "role")
