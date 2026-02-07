"""add_version_field_to_equipment

Revision ID: 1e747e89b0c0
Revises: d4a678986a16
Create Date: 2025-10-29 12:41:27.146947

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "1e747e89b0c0"
down_revision: str | Sequence[str] | None = "d4a678986a16"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("equipment", sa.Column("version", sa.String(100), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("equipment", "version")
