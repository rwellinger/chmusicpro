"""add_project_asset_relations

Revision ID: e8eb92a7820b
Revises: 281d8c3887b4
Create Date: 2025-11-01 20:57:40.613732

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "e8eb92a7820b"
down_revision: str | Sequence[str] | None = "281d8c3887b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Create project_image_references table (N:M for Images)
    op.create_table(
        "project_image_references",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("image_id", sa.UUID(), nullable=False),
        sa.Column("folder_id", sa.UUID(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["song_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["image_id"], ["generated_images.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["folder_id"], ["project_folders.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("project_id", "image_id", name="uq_project_image"),
    )
    op.create_index("ix_project_image_references_project_id", "project_image_references", ["project_id"])
    op.create_index("ix_project_image_references_image_id", "project_image_references", ["image_id"])

    # 2. Add project_folder_id to songs (1:1 relation with folder selection)
    op.add_column("songs", sa.Column("project_folder_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_songs_project_folder", "songs", "project_folders", ["project_folder_id"], ["id"], ondelete="SET NULL"
    )
    op.create_index("ix_songs_project_folder_id", "songs", ["project_folder_id"])

    # 3. Add project_folder_id to song_sketches (1:1 relation with folder selection)
    op.add_column("song_sketches", sa.Column("project_folder_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_song_sketches_project_folder",
        "song_sketches",
        "project_folders",
        ["project_folder_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_song_sketches_project_folder_id", "song_sketches", ["project_folder_id"])

    # 4. Remove generated_images.project_id (clean N:M, no backward compatibility)
    op.drop_constraint("generated_images_project_id_fkey", "generated_images", type_="foreignkey")
    op.drop_index("idx_images_project", "generated_images")
    op.drop_column("generated_images", "project_id")


def downgrade() -> None:
    """Downgrade schema."""
    # Reverse order
    # 1. Restore generated_images.project_id
    op.add_column("generated_images", sa.Column("project_id", sa.UUID(), nullable=True))
    op.create_index("idx_images_project", "generated_images", ["project_id"])
    op.create_foreign_key(
        "generated_images_project_id_fkey",
        "generated_images",
        "song_projects",
        ["project_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # 2. Remove song_sketches.project_folder_id
    op.drop_index("ix_song_sketches_project_folder_id", "song_sketches")
    op.drop_constraint("fk_song_sketches_project_folder", "song_sketches", type_="foreignkey")
    op.drop_column("song_sketches", "project_folder_id")

    # 3. Remove songs.project_folder_id
    op.drop_index("ix_songs_project_folder_id", "songs")
    op.drop_constraint("fk_songs_project_folder", "songs", type_="foreignkey")
    op.drop_column("songs", "project_folder_id")

    # 4. Drop project_image_references table
    op.drop_index("ix_project_image_references_image_id", "project_image_references")
    op.drop_index("ix_project_image_references_project_id", "project_image_references")
    op.drop_table("project_image_references")
