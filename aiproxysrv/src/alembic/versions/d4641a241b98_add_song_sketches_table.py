"""add_song_sketches_table

Revision ID: d4641a241b98
Revises: 234ea0f4b6c3
Create Date: 2025-10-20 16:50:18.116260

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d4641a241b98"
down_revision: str | Sequence[str] | None = "234ea0f4b6c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - Add song_sketches table and extend songs table."""
    # 1. Create song_sketches table
    op.create_table(
        "song_sketches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("lyrics", sa.Text(), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("tags", sa.String(1000), nullable=True),
        sa.Column("workflow", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # 2. Create indexes for song_sketches
    op.create_index("ix_song_sketches_id", "song_sketches", ["id"])
    op.create_index("ix_song_sketches_workflow", "song_sketches", ["workflow"])
    op.create_index("ix_song_sketches_created_at", "song_sketches", ["created_at"])

    # 3. Add sketch_id column to songs table
    op.add_column("songs", sa.Column("sketch_id", postgresql.UUID(as_uuid=True), nullable=True))

    # 4. Create foreign key constraint
    op.create_foreign_key("fk_songs_sketch_id", "songs", "song_sketches", ["sketch_id"], ["id"])

    # 5. Create index for sketch_id in songs
    op.create_index("ix_songs_sketch_id", "songs", ["sketch_id"])


def downgrade() -> None:
    """Downgrade schema - Remove song_sketches table and related changes."""
    # Remove foreign key and index from songs
    op.drop_constraint("fk_songs_sketch_id", "songs", type_="foreignkey")
    op.drop_index("ix_songs_sketch_id", "songs")
    op.drop_column("songs", "sketch_id")

    # Drop indexes and table for song_sketches
    op.drop_index("ix_song_sketches_created_at", "song_sketches")
    op.drop_index("ix_song_sketches_workflow", "song_sketches")
    op.drop_index("ix_song_sketches_id", "song_sketches")
    op.drop_table("song_sketches")
