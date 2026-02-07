"""add_song_release_tables

Revision ID: 28fe232c9ffd
Revises: 7ebc2fb3b04b
Create Date: 2025-11-09 11:00:44.791348

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "28fe232c9ffd"
down_revision: str | Sequence[str] | None = "7ebc2fb3b04b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Create song_releases table
    op.create_table(
        "song_releases",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),  # 'single', 'album'
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "status", sa.String(50), nullable=False, server_default="draft"
        ),  # 'draft', 'arranging', 'mixing', 'mastering', 'rejected', 'uploaded', 'released', 'downtaken', 'archived'
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("genre", sa.String(100), nullable=False),
        sa.Column("tags", sa.String(500), nullable=True),  # Comma-separated
        sa.Column("upload_date", sa.Date(), nullable=True),
        sa.Column("release_date", sa.Date(), nullable=True),
        sa.Column("downtaken_date", sa.Date(), nullable=True),
        sa.Column("downtaken_reason", sa.Text(), nullable=True),
        sa.Column("rejected_reason", sa.Text(), nullable=True),
        sa.Column("upc", sa.String(50), nullable=True),
        sa.Column("isrc", sa.String(50), nullable=True),
        sa.Column("copyright_info", sa.Text(), nullable=True),
        sa.Column("cover_s3_key", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_song_releases_user_id", "song_releases", ["user_id"])
    op.create_index("ix_song_releases_status", "song_releases", ["status"])
    op.create_index("ix_song_releases_type", "song_releases", ["type"])

    # 2. Create release_project_references table (Junction Table for Many-to-Many)
    op.create_table(
        "release_project_references",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("release_id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["release_id"], ["song_releases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["song_projects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("release_id", "project_id", name="uq_release_project"),
    )
    op.create_index("ix_release_project_references_release_id", "release_project_references", ["release_id"])
    op.create_index("ix_release_project_references_project_id", "release_project_references", ["project_id"])


def downgrade() -> None:
    """Downgrade schema."""
    # Reverse order
    # 1. Drop release_project_references table
    op.drop_index("ix_release_project_references_project_id", "release_project_references")
    op.drop_index("ix_release_project_references_release_id", "release_project_references")
    op.drop_table("release_project_references")

    # 2. Drop song_releases table
    op.drop_index("ix_song_releases_type", "song_releases")
    op.drop_index("ix_song_releases_status", "song_releases")
    op.drop_index("ix_song_releases_user_id", "song_releases")
    op.drop_table("song_releases")
