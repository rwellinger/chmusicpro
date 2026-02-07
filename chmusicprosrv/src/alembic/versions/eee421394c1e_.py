"""create_song_projects_tables

Revision ID: eee421394c1e
Revises: 6f3e14479027
Create Date: 2025-11-01 09:24:59.557122

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "eee421394c1e"
down_revision: str | Sequence[str] | None = "6f3e14479027"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Song Projects (Main)
    op.create_table(
        "song_projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("project_name", sa.String(255), nullable=False),
        # Storage
        sa.Column("s3_prefix", sa.String(255), nullable=True),
        sa.Column("local_path", sa.String(500), nullable=True),
        # Sync Status
        sa.Column("sync_status", sa.String(20), server_default="local"),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        # Metadata
        sa.Column(
            "cover_image_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("generated_images.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("tags", postgresql.ARRAY(sa.String), server_default="{}"),
        sa.Column("description", sa.Text(), nullable=True),
        # Stats
        sa.Column("total_files", sa.Integer(), server_default="0"),
        sa.Column("total_size_bytes", sa.BigInteger(), server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Project Folders
    op.create_table(
        "project_folders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("song_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("folder_name", sa.String(255), nullable=False),
        sa.Column("folder_type", sa.String(50), nullable=True),
        sa.Column("s3_prefix", sa.String(255), nullable=True),
        sa.Column("custom_icon", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Project Files
    op.create_table(
        "project_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("song_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "folder_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_folders.id", ondelete="CASCADE"),
            nullable=True,
        ),
        # File Info
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("relative_path", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(50), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        # Storage
        sa.Column("s3_key", sa.String(255), nullable=True),
        sa.Column("local_path", sa.String(500), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("file_hash", sa.String(64), nullable=True),
        # Sync
        sa.Column("storage_backend", sa.String(20), server_default="s3"),
        sa.Column("is_synced", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Indexes
    op.create_index("idx_song_projects_user", "song_projects", ["user_id"])
    op.create_index("idx_song_projects_tags", "song_projects", ["tags"], postgresql_using="gin")
    op.create_index("idx_project_files_project", "project_files", ["project_id"])
    op.create_index("idx_project_files_s3_key", "project_files", ["s3_key"])
    op.create_index("idx_project_folders_project", "project_folders", ["project_id"])

    # Add project_id to existing tables
    op.add_column(
        "song_sketches",
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("song_projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "songs",
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("song_projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "generated_images",
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("song_projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    op.create_index("idx_sketches_project", "song_sketches", ["project_id"])
    op.create_index("idx_songs_project", "songs", ["project_id"])
    op.create_index("idx_images_project", "generated_images", ["project_id"])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes on existing tables
    op.drop_index("idx_images_project")
    op.drop_index("idx_songs_project")
    op.drop_index("idx_sketches_project")

    # Drop foreign keys from existing tables
    op.drop_column("generated_images", "project_id")
    op.drop_column("songs", "project_id")
    op.drop_column("song_sketches", "project_id")

    # Drop indexes on new tables
    op.drop_index("idx_project_folders_project")
    op.drop_index("idx_project_files_s3_key")
    op.drop_index("idx_project_files_project")
    op.drop_index("idx_song_projects_tags")
    op.drop_index("idx_song_projects_user")

    # Drop tables
    op.drop_table("project_files")
    op.drop_table("project_folders")
    op.drop_table("song_projects")
