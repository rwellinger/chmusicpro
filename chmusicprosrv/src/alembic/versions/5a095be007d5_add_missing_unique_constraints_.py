"""add_missing_unique_constraints_retrospective

Revision ID: 5a095be007d5
Revises: 75b410845228
Create Date: 2025-10-21 23:36:04.864689

"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "5a095be007d5"
down_revision: str | Sequence[str] | None = "75b410845228"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - Add missing UNIQUE constraints that were manually added."""
    # These constraints were added manually to fix schema drift between DEV and PROD
    # This migration ensures they are properly tracked in Alembic history

    # Add UNIQUE constraint on lyric_parsing_rules.name (if not exists)
    # Note: Using raw SQL with IF NOT EXISTS to avoid errors on existing constraints
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_lyric_parsing_rule_name'
            ) THEN
                ALTER TABLE lyric_parsing_rules
                ADD CONSTRAINT uq_lyric_parsing_rule_name UNIQUE (name);
            END IF;
        END $$;
    """)

    # Add UNIQUE constraint on songs.task_id (if not exists)
    # Note: Constraint name matches what was manually created
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'songs_task_id_key'
            ) THEN
                ALTER TABLE songs
                ADD CONSTRAINT songs_task_id_key UNIQUE (task_id);
            END IF;
        END $$;
    """)

    # Remove redundant index on songs.task_id if it exists
    # (UNIQUE constraint already creates an implicit index)
    op.execute("""
        DROP INDEX IF EXISTS ix_songs_task_id;
    """)


def downgrade() -> None:
    """Downgrade schema - Remove UNIQUE constraints."""
    # Remove constraints
    op.drop_constraint("uq_lyric_parsing_rule_name", "lyric_parsing_rules", type_="unique")
    op.drop_constraint("songs_task_id_key", "songs", type_="unique")

    # Recreate the original index
    op.create_index("ix_songs_task_id", "songs", ["task_id"], unique=True)
