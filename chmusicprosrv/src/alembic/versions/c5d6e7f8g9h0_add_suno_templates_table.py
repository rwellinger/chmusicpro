"""add_suno_templates_table

Revision ID: c5d6e7f8g9h0
Revises: b4c7d8e9f0a1
Create Date: 2026-02-22 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c5d6e7f8g9h0"
down_revision: str | Sequence[str] | None = "b4c7d8e9f0a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - Add suno_templates table."""
    op.create_table(
        "suno_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        # Domain ownership (multi-tenancy)
        sa.Column("domain_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("domains.id"), nullable=False),
        # User reference
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        # Template metadata
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("template_type", sa.String(20), nullable=False, server_default="song"),
        # Source sketch (Song-Modus only)
        sa.Column(
            "source_sketch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("song_sketches.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # Lyrics
        sa.Column("original_lyrics", sa.Text(), nullable=True),
        sa.Column("enhanced_lyrics", sa.Text(), nullable=True),
        # Style fields
        sa.Column("genre", sa.String(200), nullable=True),
        sa.Column("bpm", sa.Integer(), nullable=True),
        sa.Column("vocal_type", sa.String(100), nullable=True),
        sa.Column("instruments", sa.Text(), nullable=True),
        sa.Column("mood", sa.String(500), nullable=True),
        sa.Column("mix_character", sa.String(200), nullable=True),
        sa.Column("style_prompt", sa.Text(), nullable=True),
        sa.Column("is_instrumental", sa.Boolean(), nullable=False, server_default="false"),
        # Project relationship (optional)
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("song_projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "project_folder_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_folders.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes
    op.create_index("ix_suno_templates_id", "suno_templates", ["id"])
    op.create_index("ix_suno_templates_domain_id", "suno_templates", ["domain_id"])
    op.create_index("ix_suno_templates_user_id", "suno_templates", ["user_id"])
    op.create_index("ix_suno_templates_template_type", "suno_templates", ["template_type"])
    op.create_index("ix_suno_templates_created_at", "suno_templates", ["created_at"])


def downgrade() -> None:
    """Downgrade schema - Remove suno_templates table."""
    op.drop_index("ix_suno_templates_created_at", "suno_templates")
    op.drop_index("ix_suno_templates_template_type", "suno_templates")
    op.drop_index("ix_suno_templates_user_id", "suno_templates")
    op.drop_index("ix_suno_templates_domain_id", "suno_templates")
    op.drop_index("ix_suno_templates_id", "suno_templates")
    op.drop_table("suno_templates")
