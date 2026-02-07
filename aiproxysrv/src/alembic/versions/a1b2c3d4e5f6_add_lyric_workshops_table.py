"""add_lyric_workshops_table

Revision ID: a1b2c3d4e5f6
Revises: 457ba43d7309
Create Date: 2026-02-06 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "457ba43d7309"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - Add lyric_workshops table."""
    op.create_table(
        "lyric_workshops",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(200), nullable=False),
        # Phase 1: Connect
        sa.Column("connect_topic", sa.Text(), nullable=True),
        sa.Column("connect_inspirations", sa.Text(), nullable=True),
        # Phase 2: Collect
        sa.Column("collect_mindmap", sa.Text(), nullable=True),
        sa.Column("collect_stories", sa.Text(), nullable=True),
        sa.Column("collect_words", sa.Text(), nullable=True),
        # Phase 3: Shape
        sa.Column("shape_structure", sa.Text(), nullable=True),
        sa.Column("shape_rhymes", sa.Text(), nullable=True),
        sa.Column("shape_draft", sa.Text(), nullable=True),
        # Meta
        sa.Column("current_phase", sa.String(20), nullable=False, server_default="connect"),
        sa.Column(
            "exported_sketch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("song_sketches.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes
    op.create_index("ix_lyric_workshops_id", "lyric_workshops", ["id"])
    op.create_index("ix_lyric_workshops_current_phase", "lyric_workshops", ["current_phase"])
    op.create_index("ix_lyric_workshops_created_at", "lyric_workshops", ["created_at"])


def downgrade() -> None:
    """Downgrade schema - Remove lyric_workshops table."""
    op.drop_index("ix_lyric_workshops_created_at", "lyric_workshops")
    op.drop_index("ix_lyric_workshops_current_phase", "lyric_workshops")
    op.drop_index("ix_lyric_workshops_id", "lyric_workshops")
    op.drop_table("lyric_workshops")
