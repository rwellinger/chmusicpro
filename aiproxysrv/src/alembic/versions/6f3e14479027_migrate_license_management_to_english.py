"""migrate_license_management_to_english

Revision ID: 6f3e14479027
Revises: 1e747e89b0c0
Create Date: 2025-10-29 12:54:12.775182

"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "6f3e14479027"
down_revision: str | Sequence[str] | None = "1e747e89b0c0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Migrate license_management values from German to English."""
    # Mapping: German -> English
    # 'Online' -> 'online'
    # 'iLok' -> 'ilok'
    # 'Lizenzschlüssel' -> 'license_key'
    # 'andere' -> 'other'

    op.execute("""
        UPDATE equipment
        SET license_management = CASE
            WHEN license_management = 'Online' THEN 'online'
            WHEN license_management = 'iLok' THEN 'ilok'
            WHEN license_management = 'Lizenzschlüssel' THEN 'license_key'
            WHEN license_management = 'andere' THEN 'other'
            ELSE license_management
        END
        WHERE license_management IN ('Online', 'iLok', 'Lizenzschlüssel', 'andere')
    """)


def downgrade() -> None:
    """Rollback: Migrate license_management values from English to German."""
    op.execute("""
        UPDATE equipment
        SET license_management = CASE
            WHEN license_management = 'online' THEN 'Online'
            WHEN license_management = 'ilok' THEN 'iLok'
            WHEN license_management = 'license_key' THEN 'Lizenzschlüssel'
            WHEN license_management = 'other' THEN 'andere'
            ELSE license_management
        END
        WHERE license_management IN ('online', 'ilok', 'license_key', 'other')
    """)
