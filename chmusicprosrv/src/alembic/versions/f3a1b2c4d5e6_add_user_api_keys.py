"""add_user_api_keys

Revision ID: f3a1b2c4d5e6
Revises: 0a902dbe6d06
Create Date: 2026-02-17 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f3a1b2c4d5e6"
down_revision: str | Sequence[str] | None = "0a902dbe6d06"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("openai_api_key_encrypted", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("openai_admin_api_key_encrypted", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("claude_api_key_encrypted", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "claude_api_key_encrypted")
    op.drop_column("users", "openai_admin_api_key_encrypted")
    op.drop_column("users", "openai_api_key_encrypted")
