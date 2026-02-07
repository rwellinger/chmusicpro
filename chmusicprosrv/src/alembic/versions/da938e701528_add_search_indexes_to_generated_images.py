"""add_search_indexes_to_generated_images

Revision ID: da938e701528
Revises: ad849273b893
Create Date: 2025-09-19 12:00:59.411716

"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "da938e701528"
down_revision: str | Sequence[str] | None = "ad849273b893"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Enable pg_trgm extension for better text search performance
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    # Composite index for the most common query pattern: sort by created_at with search
    op.create_index(
        "idx_generated_images_created_search",
        "generated_images",
        ["created_at", "title", "prompt"],
        postgresql_using="btree",
    )

    # GIN indexes for efficient ILIKE text search on title and prompt
    op.create_index(
        "idx_generated_images_title_gin",
        "generated_images",
        ["title"],
        postgresql_using="gin",
        postgresql_ops={"title": "gin_trgm_ops"},
    )

    op.create_index(
        "idx_generated_images_prompt_gin",
        "generated_images",
        ["prompt"],
        postgresql_using="gin",
        postgresql_ops={"prompt": "gin_trgm_ops"},
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the indexes in reverse order
    op.drop_index("idx_generated_images_prompt_gin", "generated_images")
    op.drop_index("idx_generated_images_title_gin", "generated_images")
    op.drop_index("idx_generated_images_created_search", "generated_images")

    # Note: We don't drop the pg_trgm extension as it might be used by other parts
