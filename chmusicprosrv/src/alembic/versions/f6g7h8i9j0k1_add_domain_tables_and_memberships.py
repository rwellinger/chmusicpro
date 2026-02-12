"""Add domain tables and memberships for multi-tenancy

Revision ID: f6g7h8i9j0k1
Revises: e5f6g7h8i9j0
Create Date: 2026-02-12

Multi-Tenancy V2: Replace user-based isolation with domain-based multi-tenancy.
Creates domains + domain_memberships tables, migrates existing data to personal domains,
adds domain_id to all entity tables.
"""

import uuid

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID

from alembic import op


# revision identifiers, used by Alembic.
revision = "f6g7h8i9j0k1"
down_revision = "e5f6g7h8i9j0"
branch_labels = None
depends_on = None

# Entity tables that get domain_id (NOT NULL after backfill)
ENTITY_TABLES = [
    "song_sketches",
    "lyric_workshops",
    "generated_images",
    "equipment",
    "equipment_attachments",
    "song_projects",
    "song_releases",
    "conversations",
]

# Admin tables that get domain_id (nullable, set to reserved domain)
ADMIN_TABLES = [
    "prompt_templates",
    "lyric_parsing_rules",
]


def upgrade() -> None:
    # --- Step 1: Create domains table ---
    op.create_table(
        "domains",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("type", sa.Integer, nullable=False),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_domains_id", "domains", ["id"])
    op.create_index("ix_domains_type", "domains", ["type"])

    # --- Step 2: Create domain_memberships table ---
    op.create_table(
        "domain_memberships",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("domain_id", UUID(as_uuid=True), sa.ForeignKey("domains.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="member"),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("domain_id", "user_id", name="uq_domain_user"),
    )
    op.create_index("ix_domain_memberships_id", "domain_memberships", ["id"])
    op.create_index("ix_domain_memberships_domain_id", "domain_memberships", ["domain_id"])
    op.create_index("ix_domain_memberships_user_id", "domain_memberships", ["user_id"])

    # --- Step 3: Insert reserved domains ---
    connection = op.get_bind()

    system_domain_id = str(uuid.uuid4())
    ki_templates_domain_id = str(uuid.uuid4())

    connection.execute(
        text(
            "INSERT INTO domains (id, type, name, description) "
            "VALUES (:id, 0, 'System', 'System administration domain')"
        ),
        {"id": system_domain_id},
    )
    connection.execute(
        text(
            "INSERT INTO domains (id, type, name, description) "
            "VALUES (:id, 1, 'KI Templates', 'AI prompt templates and configuration')"
        ),
        {"id": ki_templates_domain_id},
    )

    # --- Step 4: Create personal domains + memberships for all existing users ---
    users = connection.execute(text("SELECT id, email, role FROM users")).fetchall()

    for user in users:
        user_id = str(user[0])
        user_email = user[1]
        user_role = user[2]

        # Create personal domain (type=2)
        personal_domain_id = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO domains (id, type, name, description) VALUES (:id, 2, :name, :description)"),
            {
                "id": personal_domain_id,
                "name": f"user:{user_email}",
                "description": f"Personal domain for {user_email}",
            },
        )

        # Membership: personal domain (owner, is_default=true)
        connection.execute(
            text(
                "INSERT INTO domain_memberships (id, domain_id, user_id, role, is_default) "
                "VALUES (:id, :domain_id, :user_id, 'owner', true)"
            ),
            {"id": str(uuid.uuid4()), "domain_id": personal_domain_id, "user_id": user_id},
        )

        # Membership: System domain (viewer by default, admin if user is admin)
        system_role = "admin" if user_role == "admin" else "viewer"
        connection.execute(
            text(
                "INSERT INTO domain_memberships (id, domain_id, user_id, role, is_default) "
                "VALUES (:id, :domain_id, :user_id, :role, false)"
            ),
            {
                "id": str(uuid.uuid4()),
                "domain_id": system_domain_id,
                "user_id": user_id,
                "role": system_role,
            },
        )

        # Membership: KI Templates domain (viewer by default, admin if user is admin)
        ki_role = "admin" if user_role == "admin" else "viewer"
        connection.execute(
            text(
                "INSERT INTO domain_memberships (id, domain_id, user_id, role, is_default) "
                "VALUES (:id, :domain_id, :user_id, :role, false)"
            ),
            {
                "id": str(uuid.uuid4()),
                "domain_id": ki_templates_domain_id,
                "user_id": user_id,
                "role": ki_role,
            },
        )

    # --- Step 5: Add domain_id to entity tables (nullable first) ---
    for table in ENTITY_TABLES:
        op.add_column(table, sa.Column("domain_id", UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(f"fk_{table}_domain_id", table, "domains", ["domain_id"], ["id"])
        op.create_index(f"ix_{table}_domain_id", table, ["domain_id"])

    # --- Step 6: Backfill entity tables from user's default (personal) domain ---
    for table in ENTITY_TABLES:
        connection.execute(
            text(
                f"UPDATE {table} SET domain_id = ("  # noqa: S608
                "  SELECT dm.domain_id FROM domain_memberships dm "
                f"  WHERE dm.user_id = {table}.user_id AND dm.is_default = true "
                "  LIMIT 1"
                f") WHERE {table}.domain_id IS NULL"
            )
        )

    # --- Step 7: Set NOT NULL on entity tables ---
    for table in ENTITY_TABLES:
        op.alter_column(table, "domain_id", nullable=False)

    # --- Step 8: Add domain_id to admin tables (nullable, set to reserved domain) ---
    for table in ADMIN_TABLES:
        op.add_column(table, sa.Column("domain_id", UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(f"fk_{table}_domain_id", table, "domains", ["domain_id"], ["id"])
        op.create_index(f"ix_{table}_domain_id", table, ["domain_id"])

    # Set prompt_templates to KI Templates domain
    connection.execute(
        text("UPDATE prompt_templates SET domain_id = :domain_id"),
        {"domain_id": ki_templates_domain_id},
    )
    # Set lyric_parsing_rules to System domain
    connection.execute(
        text("UPDATE lyric_parsing_rules SET domain_id = :domain_id"),
        {"domain_id": system_domain_id},
    )


def downgrade() -> None:
    # Remove domain_id from admin tables
    for table in ADMIN_TABLES:
        op.drop_index(f"ix_{table}_domain_id", table_name=table)
        op.drop_constraint(f"fk_{table}_domain_id", table, type_="foreignkey")
        op.drop_column(table, "domain_id")

    # Remove domain_id from entity tables
    for table in ENTITY_TABLES:
        op.drop_index(f"ix_{table}_domain_id", table_name=table)
        op.drop_constraint(f"fk_{table}_domain_id", table, type_="foreignkey")
        op.drop_column(table, "domain_id")

    # Drop domain_memberships
    op.drop_index("ix_domain_memberships_user_id", table_name="domain_memberships")
    op.drop_index("ix_domain_memberships_domain_id", table_name="domain_memberships")
    op.drop_index("ix_domain_memberships_id", table_name="domain_memberships")
    op.drop_table("domain_memberships")

    # Drop domains
    op.drop_index("ix_domains_type", table_name="domains")
    op.drop_index("ix_domains_id", table_name="domains")
    op.drop_table("domains")
