"""Create provider-neutral integration entity mappings.

Revision ID: 20260921_integration_mappings
Revises: 20260921_integration_events
Create Date: 2026-09-21
"""
from alembic import op
import sqlalchemy as sa

revision = "20260921_integration_mappings"
down_revision = "20260921_integration_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "integration_mappings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("connection_id", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.String(length=120), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("local_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint(
            "company_id", "connection_id", "entity_type", "external_id",
            name="uq_integration_mappings_external_identity",
        ),
    )
    op.create_index("ix_integration_mappings_company_id", "integration_mappings", ["company_id"])
    op.create_index("ix_integration_mappings_connection_id", "integration_mappings", ["connection_id"])
    op.create_index("ix_integration_mappings_entity_type", "integration_mappings", ["entity_type"])
    op.create_index("ix_integration_mappings_external_id", "integration_mappings", ["external_id"])
    op.create_index("ix_integration_mappings_local_id", "integration_mappings", ["local_id"])


def downgrade() -> None:
    op.drop_index("ix_integration_mappings_local_id", table_name="integration_mappings")
    op.drop_index("ix_integration_mappings_external_id", table_name="integration_mappings")
    op.drop_index("ix_integration_mappings_entity_type", table_name="integration_mappings")
    op.drop_index("ix_integration_mappings_connection_id", table_name="integration_mappings")
    op.drop_index("ix_integration_mappings_company_id", table_name="integration_mappings")
    op.drop_table("integration_mappings")
