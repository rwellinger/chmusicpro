"""add_s3_storage_fields_to_images

Revision ID: 281d8c3887b4
Revises: eee421394c1e
Create Date: 2025-11-01 12:12:53.284097

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "281d8c3887b4"
down_revision: str | Sequence[str] | None = "eee421394c1e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add S3 storage fields to generated_images table."""
    # Add s3_key column (nullable for backward compatibility with filesystem images)
    op.add_column("generated_images", sa.Column("s3_key", sa.String(length=500), nullable=True))

    # Add storage_backend column (default 'filesystem' for existing rows)
    op.add_column(
        "generated_images",
        sa.Column("storage_backend", sa.String(length=20), server_default="filesystem", nullable=False),
    )


def downgrade() -> None:
    """Remove S3 storage fields from generated_images table."""
    op.drop_column("generated_images", "storage_backend")
    op.drop_column("generated_images", "s3_key")
