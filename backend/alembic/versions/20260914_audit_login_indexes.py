"""Add composite indexes used by authentication throttling.

Revision ID: 20260914_audit_login_indexes
Revises: 20260914_plan_default_guard
"""

from alembic import op


revision = "20260914_audit_login_indexes"
down_revision = "20260914_plan_default_guard"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "ix_audit_login_failure_account",
        "audit_events",
        ["action", "entity_type", "entity_id", "created_at"],
    )
    op.create_index(
        "ix_audit_login_failure_ip",
        "audit_events",
        ["action", "ip_address", "created_at"],
    )


def downgrade():
    op.drop_index("ix_audit_login_failure_ip", table_name="audit_events")
    op.drop_index("ix_audit_login_failure_account", table_name="audit_events")
