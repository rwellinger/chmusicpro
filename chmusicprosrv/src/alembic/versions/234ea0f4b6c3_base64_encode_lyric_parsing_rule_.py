"""base64_encode_lyric_parsing_rule_replacements

Revision ID: 234ea0f4b6c3
Revises: 0f864573b58a
Create Date: 2025-10-18 12:03:27.669862

"""

import base64
from collections.abc import Sequence

from sqlalchemy import text

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "234ea0f4b6c3"
down_revision: str | Sequence[str] | None = "0f864573b58a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Encode all existing replacement strings to Base64"""
    # Get database connection
    conn = op.get_bind()

    # Fetch all lyric_parsing_rules
    result = conn.execute(text("SELECT id, replacement FROM lyric_parsing_rules"))

    # Encode each replacement value
    for row in result:
        rule_id = row[0]
        original_replacement = row[1]

        # Skip if already Base64 (basic check: try to decode)
        try:
            base64.b64decode(original_replacement.encode()).decode("utf-8")
            # If successful, assume it's already encoded (skip)
            continue
        except Exception:
            # Not valid Base64, encode it
            encoded_replacement = base64.b64encode(original_replacement.encode("utf-8")).decode("ascii")

            # Update the row
            conn.execute(
                text("UPDATE lyric_parsing_rules SET replacement = :replacement WHERE id = :id"),
                {"replacement": encoded_replacement, "id": rule_id},
            )

    # Commit the transaction
    conn.commit()


def downgrade() -> None:
    """Decode all Base64-encoded replacement strings back to plain text"""
    # Get database connection
    conn = op.get_bind()

    # Fetch all lyric_parsing_rules
    result = conn.execute(text("SELECT id, replacement FROM lyric_parsing_rules"))

    # Decode each replacement value
    for row in result:
        rule_id = row[0]
        encoded_replacement = row[1]

        # Try to decode from Base64
        try:
            decoded_replacement = base64.b64decode(encoded_replacement.encode()).decode("utf-8")

            # Update the row
            conn.execute(
                text("UPDATE lyric_parsing_rules SET replacement = :replacement WHERE id = :id"),
                {"replacement": decoded_replacement, "id": rule_id},
            )
        except Exception:
            # If decode fails, skip (already plain text)
            continue

    # Commit the transaction
    conn.commit()
