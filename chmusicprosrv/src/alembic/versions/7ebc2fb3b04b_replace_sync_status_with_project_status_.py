"""replace_sync_status_with_project_status_and_cleanup_obsolete_fields

Revision ID: 7ebc2fb3b04b
Revises: e8eb92a7820b
Create Date: 2025-11-06 12:39:47.856959

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "7ebc2fb3b04b"
down_revision: str | Sequence[str] | None = "e8eb92a7820b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema: Replace sync_status with project_status, remove obsolete fields, add performance indexes."""

    # 1. Add new project_status column (default: 'progress' for all existing projects)
    op.add_column(
        "song_projects", sa.Column("project_status", sa.String(20), nullable=False, server_default="progress")
    )

    # 2. Drop obsolete columns (sync status and cached stats)
    op.drop_column("song_projects", "sync_status")
    op.drop_column("song_projects", "last_sync_at")
    op.drop_column("song_projects", "total_files")
    op.drop_column("song_projects", "total_size_bytes")

    # 3. Performance indexes
    # GIN Index for text search (ILIKE queries on project_name)
    op.execute("""
        CREATE INDEX ix_song_projects_project_name_gin
        ON song_projects
        USING gin (project_name gin_trgm_ops)
    """)

    # B-Tree Index for Mirror Sync (file_hash lookups)
    op.create_index("ix_project_files_file_hash", "project_files", ["file_hash"], unique=False)


def downgrade() -> None:
    """Downgrade schema: Restore sync_status and obsolete fields."""

    # 1. Drop performance indexes
    op.drop_index("ix_project_files_file_hash", table_name="project_files")
    op.execute("DROP INDEX IF EXISTS ix_song_projects_project_name_gin")

    # 2. Restore obsolete columns
    op.add_column("song_projects", sa.Column("total_size_bytes", sa.Integer(), server_default="0"))
    op.add_column("song_projects", sa.Column("total_files", sa.Integer(), server_default="0"))
    op.add_column("song_projects", sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("song_projects", sa.Column("sync_status", sa.String(20), server_default="local"))

    # 3. Drop project_status column
    op.drop_column("song_projects", "project_status")
