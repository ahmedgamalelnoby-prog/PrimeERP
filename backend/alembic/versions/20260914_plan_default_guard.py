"""Enforce a single default platform plan at the database level.

Revision ID: 20260914_plan_default_guard
Revises: 20260913_salla_erp_execution
"""

from alembic import op


revision = "20260914_plan_default_guard"
down_revision = "20260913_salla_erp_execution"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "ux_plans_single_default",
        "plans",
        ["is_default"],
        unique=True,
        postgresql_where="is_default = true",
    )


def downgrade():
    op.drop_index("ux_plans_single_default", table_name="plans")
