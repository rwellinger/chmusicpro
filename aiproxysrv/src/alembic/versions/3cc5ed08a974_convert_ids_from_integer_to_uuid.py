"""Convert IDs from Integer to UUID

Revision ID: 3cc5ed08a974
Revises: aaef2a47784e
Create Date: 2025-09-12 15:05:59.099228

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "3cc5ed08a974"
down_revision: str | Sequence[str] | None = "aaef2a47784e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Drop existing tables and recreate with UUIDs (since data can be deleted)
    op.drop_table("song_choices")
    op.drop_table("songs")
    op.drop_table("generated_images")

    # Recreate songs table with UUID
    op.create_table(
        "songs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("task_id", sa.String(255), nullable=False, unique=True),
        sa.Column("job_id", sa.String(255), nullable=True),
        sa.Column("lyrics", sa.Text, nullable=False),
        sa.Column("prompt", sa.Text, nullable=False),
        sa.Column("model", sa.String(100), nullable=True, default="chirp-v3-5"),
        sa.Column("status", sa.String(50), nullable=False, default="PENDING"),
        sa.Column("progress_info", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("mureka_response", sa.Text, nullable=True),
        sa.Column("mureka_status", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Recreate song_choices table with UUID
    op.create_table(
        "song_choices",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("song_id", UUID(as_uuid=True), nullable=False),
        sa.Column("mureka_choice_id", sa.String(255), nullable=True),
        sa.Column("choice_index", sa.Integer, nullable=True),
        sa.Column("mp3_url", sa.String(1000), nullable=True),
        sa.Column("flac_url", sa.String(1000), nullable=True),
        sa.Column("video_url", sa.String(1000), nullable=True),
        sa.Column("image_url", sa.String(1000), nullable=True),
        sa.Column("duration", sa.Float, nullable=True),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("tags", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(["song_id"], ["songs.id"]),
    )

    # Recreate generated_images table with UUID
    op.create_table(
        "generated_images",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("prompt", sa.Text, nullable=False),
        sa.Column("size", sa.String(20), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False, unique=True),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("local_url", sa.String(500), nullable=False),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("prompt_hash", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # Recreate indexes
    op.create_index("ix_songs_id", "songs", ["id"])
    op.create_index("ix_songs_task_id", "songs", ["task_id"])
    op.create_index("ix_songs_job_id", "songs", ["job_id"])
    op.create_index("ix_song_choices_id", "song_choices", ["id"])
    op.create_index("ix_song_choices_song_id", "song_choices", ["song_id"])
    op.create_index("ix_generated_images_id", "generated_images", ["id"])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables with UUID IDs
    op.drop_table("song_choices")
    op.drop_table("songs")
    op.drop_table("generated_images")

    # Recreate tables with Integer IDs (original structure)
    op.create_table(
        "songs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("task_id", sa.String(255), nullable=False, unique=True),
        sa.Column("job_id", sa.String(255), nullable=True),
        sa.Column("lyrics", sa.Text, nullable=False),
        sa.Column("prompt", sa.Text, nullable=False),
        sa.Column("model", sa.String(100), nullable=True, default="chirp-v3-5"),
        sa.Column("status", sa.String(50), nullable=False, default="PENDING"),
        sa.Column("progress_info", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("mureka_response", sa.Text, nullable=True),
        sa.Column("mureka_status", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "song_choices",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("song_id", sa.Integer, nullable=False),
        sa.Column("mureka_choice_id", sa.String(255), nullable=True),
        sa.Column("choice_index", sa.Integer, nullable=True),
        sa.Column("mp3_url", sa.String(1000), nullable=True),
        sa.Column("flac_url", sa.String(1000), nullable=True),
        sa.Column("video_url", sa.String(1000), nullable=True),
        sa.Column("image_url", sa.String(1000), nullable=True),
        sa.Column("duration", sa.Float, nullable=True),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("tags", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(["song_id"], ["songs.id"]),
    )

    op.create_table(
        "generated_images",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("prompt", sa.Text, nullable=False),
        sa.Column("size", sa.String(20), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False, unique=True),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("local_url", sa.String(500), nullable=False),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("prompt_hash", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
