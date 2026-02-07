"""add_equipment_attachments

Revision ID: 670a6ec6cf57
Revises: 17d0668cedbe
Create Date: 2025-12-10 17:30:22.254399

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "670a6ec6cf57"
down_revision: str | Sequence[str] | None = "17d0668cedbe"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create equipment_attachments table
    op.create_table(
        "equipment_attachments",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("equipment_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("s3_key", sa.String(500), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_equipment_attachments_equipment_id", "equipment_attachments", ["equipment_id"])
    op.create_index("ix_equipment_attachments_user_id", "equipment_attachments", ["user_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_equipment_attachments_user_id", "equipment_attachments")
    op.drop_index("ix_equipment_attachments_equipment_id", "equipment_attachments")
    op.drop_table("equipment_attachments")
