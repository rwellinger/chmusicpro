"""Add user_id to song_sketches, lyric_workshops, generated_images

Revision ID: c3d4e5f6g7h8
Revises: 09b25057ccbd
Create Date: 2026-02-08

Multi-Tenancy Phase 1: Add user_id column with FK to users.id
for data isolation per user.
"""

import sqlalchemy as sa
from sqlalchemy import text  # noqa: I001
from sqlalchemy.dialects.postgresql import UUID

from alembic import op


# revision identifiers, used by Alembic.
revision = "c3d4e5f6g7h8"
down_revision = "09b25057ccbd"
branch_labels = None
depends_on = None

TABLES = ["song_sketches", "lyric_workshops", "generated_images"]


def upgrade() -> None:
    # Step 1: Add nullable user_id columns with FK and index
    for table in TABLES:
        op.add_column(table, sa.Column("user_id", UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(
            f"fk_{table}_user_id",
            table,
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )
        op.create_index(f"ix_{table}_user_id", table, ["user_id"])

    # Step 2: Backfill - assign all existing rows to first active user
    connection = op.get_bind()
    first_user = connection.execute(
        text("SELECT id FROM users WHERE is_active = true ORDER BY created_at ASC LIMIT 1")
    ).fetchone()

    if first_user:
        user_id = str(first_user[0])
        for table in TABLES:
            connection.execute(
                text(f"UPDATE {table} SET user_id = :user_id WHERE user_id IS NULL"),
                {"user_id": user_id},
            )

    # Step 3: Set NOT NULL after backfill
    for table in TABLES:
        op.alter_column(table, "user_id", nullable=False)


def downgrade() -> None:
    for table in TABLES:
        op.drop_index(f"ix_{table}_user_id", table_name=table)
        op.drop_constraint(f"fk_{table}_user_id", table, type_="foreignkey")
        op.drop_column(table, "user_id")
