"""Add project assignment to lyric_workshops

Revision ID: 0a902dbe6d06
Revises: 0477eae07283
Create Date: 2026-02-17 12:42:21.418370

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0a902dbe6d06"
down_revision: str | Sequence[str] | None = "0477eae07283"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add project_id and project_folder_id columns to lyric_workshops."""
    op.add_column("lyric_workshops", sa.Column("project_id", sa.UUID(), nullable=True))
    op.add_column("lyric_workshops", sa.Column("project_folder_id", sa.UUID(), nullable=True))
    op.create_index(op.f("ix_lyric_workshops_project_id"), "lyric_workshops", ["project_id"], unique=False)
    op.create_index(
        op.f("ix_lyric_workshops_project_folder_id"), "lyric_workshops", ["project_folder_id"], unique=False
    )
    op.create_foreign_key(
        "fk_lyric_workshops_project_id", "lyric_workshops", "song_projects", ["project_id"], ["id"], ondelete="SET NULL"
    )
    op.create_foreign_key(
        "fk_lyric_workshops_project_folder_id",
        "lyric_workshops",
        "project_folders",
        ["project_folder_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Remove project assignment from lyric_workshops."""
    op.drop_constraint("fk_lyric_workshops_project_folder_id", "lyric_workshops", type_="foreignkey")
    op.drop_constraint("fk_lyric_workshops_project_id", "lyric_workshops", type_="foreignkey")
    op.drop_index(op.f("ix_lyric_workshops_project_folder_id"), table_name="lyric_workshops")
    op.drop_index(op.f("ix_lyric_workshops_project_id"), table_name="lyric_workshops")
    op.drop_column("lyric_workshops", "project_folder_id")
    op.drop_column("lyric_workshops", "project_id")
