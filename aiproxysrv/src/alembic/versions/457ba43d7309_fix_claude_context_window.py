"""fix_claude_context_window

Fix context_window_size for existing Claude conversations.

Previously, Claude conversations were created with context_window_size=2048
(default fallback) instead of the correct 200,000 tokens.

This migration updates all existing Claude conversations to have the correct
context window size of 200,000 tokens.

Revision ID: 457ba43d7309
Revises: 8bbbad800c3b
Create Date: 2026-01-06 09:20:34.924101

"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "457ba43d7309"
down_revision: str | Sequence[str] | None = "8bbbad800c3b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Update existing Claude conversations to have correct context window (200k)."""
    op.execute(
        """
        UPDATE conversations
        SET context_window_size = 200000
        WHERE external_provider = 'claude'
          AND context_window_size != 200000
        """
    )


def downgrade() -> None:
    """Revert Claude conversations to old default (2048)."""
    op.execute(
        """
        UPDATE conversations
        SET context_window_size = 2048
        WHERE external_provider = 'claude'
          AND context_window_size = 200000
        """
    )
