"""add_search_indexes_to_songs

Revision ID: ce70bed82146
Revises: da938e701528
Create Date: 2025-09-19 13:02:24.074661

"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "ce70bed82146"
down_revision: str | Sequence[str] | None = "da938e701528"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Enable pg_trgm extension for better text search performance (idempotent)
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    # Composite index for the most common query pattern: sort by created_at with search
    op.create_index("idx_songs_created_search", "songs", ["created_at", "title", "lyrics"], postgresql_using="btree")

    # GIN indexes for efficient ILIKE text search on title, lyrics, and tags
    op.create_index(
        "idx_songs_title_gin", "songs", ["title"], postgresql_using="gin", postgresql_ops={"title": "gin_trgm_ops"}
    )

    op.create_index(
        "idx_songs_lyrics_gin", "songs", ["lyrics"], postgresql_using="gin", postgresql_ops={"lyrics": "gin_trgm_ops"}
    )

    op.create_index(
        "idx_songs_tags_gin", "songs", ["tags"], postgresql_using="gin", postgresql_ops={"tags": "gin_trgm_ops"}
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the indexes in reverse order
    op.drop_index("idx_songs_tags_gin", "songs")
    op.drop_index("idx_songs_lyrics_gin", "songs")
    op.drop_index("idx_songs_title_gin", "songs")
    op.drop_index("idx_songs_created_search", "songs")

    # Note: We don't drop the pg_trgm extension as it might be used by other parts
