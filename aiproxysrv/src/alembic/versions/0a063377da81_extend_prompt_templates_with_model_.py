"""extend_prompt_templates_with_model_temperature_max_tokens

Revision ID: 0a063377da81
Revises: 78f60c60052e
Create Date: 2025-09-23 12:44:26.584726

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0a063377da81"
down_revision: str | Sequence[str] | None = "78f60c60052e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - extend prompt_templates with model, temperature, max_tokens."""
    # Rename model_hint to model
    op.alter_column("prompt_templates", "model_hint", new_column_name="model")

    # Add temperature field (float, nullable, for Ollama Chat API values 0.0-2.0)
    op.add_column("prompt_templates", sa.Column("temperature", sa.Float, nullable=True))

    # Add max_tokens field (integer, nullable)
    op.add_column("prompt_templates", sa.Column("max_tokens", sa.Integer, nullable=True))


def downgrade() -> None:
    """Downgrade schema - revert prompt_templates changes."""
    # Remove new columns
    op.drop_column("prompt_templates", "max_tokens")
    op.drop_column("prompt_templates", "temperature")

    # Rename model back to model_hint
    op.alter_column("prompt_templates", "model", new_column_name="model_hint")
