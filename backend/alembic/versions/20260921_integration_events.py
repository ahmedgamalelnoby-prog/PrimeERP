"""Create durable integration event queue storage.

Revision ID: 20260921_integration_events
Revises: 20260911_odoo_module_catalog
Create Date: 2026-09-21
"""
from alembic import op
import sqlalchemy as sa

revision = "20260921_integration_events"
down_revision = "20260911_odoo_module_catalog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "integration_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=120), nullable=False, server_default="generic"),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="received"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_integration_events_company_id", "integration_events", ["company_id"])
    op.create_index("ix_integration_events_external_id", "integration_events", ["external_id"])
    op.create_index("ix_integration_events_status", "integration_events", ["status"])
    op.create_index("ix_integration_events_next_attempt_at", "integration_events", ["next_attempt_at"])


def downgrade() -> None:
    op.drop_index("ix_integration_events_next_attempt_at", table_name="integration_events")
    op.drop_index("ix_integration_events_status", table_name="integration_events")
    op.drop_index("ix_integration_events_external_id", table_name="integration_events")
    op.drop_index("ix_integration_events_company_id", table_name="integration_events")
    op.drop_table("integration_events")
