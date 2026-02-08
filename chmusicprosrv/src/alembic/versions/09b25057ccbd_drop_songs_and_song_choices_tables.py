"""drop_songs_and_song_choices_tables

Remove orphaned songs and song_choices tables.
These were used for Mureka song generation which has been removed.

Revision ID: 09b25057ccbd
Revises: b2c3d4e5f6g7
Create Date: 2026-02-08 17:17:27.646663

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "09b25057ccbd"
down_revision: str | None = "b2c3d4e5f6g7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop song_choices first (FK dependency), then songs."""
    op.drop_table("song_choices")
    op.drop_table("songs")


def downgrade() -> None:
    """Recreate songs and song_choices tables with original schema."""
    op.create_table(
        "songs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("sketch_id", sa.String(length=36), nullable=True),
        sa.Column("project_id", sa.String(length=36), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("tags", postgresql.JSONB(), nullable=True),
        sa.Column("model", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("workflow", sa.String(length=20), nullable=False, server_default="notUsed"),
        sa.Column("is_instrumental", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["sketch_id"], ["song_sketches.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["song_projects.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_songs_user_id", "songs", ["user_id"])
    op.create_index("ix_songs_status", "songs", ["status"])
    op.create_index("ix_songs_created_at", "songs", ["created_at"])
    op.create_index("ix_songs_workflow", "songs", ["workflow"])

    op.create_table(
        "song_choices",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("song_id", sa.String(length=36), nullable=False),
        sa.Column("audio_url", sa.Text(), nullable=True),
        sa.Column("video_url", sa.Text(), nullable=True),
        sa.Column("s3_mp3_key", sa.String(length=500), nullable=True),
        sa.Column("s3_flac_key", sa.String(length=500), nullable=True),
        sa.Column("s3_wav_key", sa.String(length=500), nullable=True),
        sa.Column("s3_stem_key", sa.String(length=500), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("lyrics", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["song_id"], ["songs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_song_choices_song_id", "song_choices", ["song_id"])
