"""Enforce one payroll run per company and payroll period.

Revision ID: 20260920_enterprise_payroll_period_guard
Revises: 20260920_enterprise_business_key_guards
"""
from alembic import op

revision = "20260920_enterprise_payroll_period_guard"
down_revision = "20260920_enterprise_business_key_guards"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint(
        "uq_payroll_runs_company_period",
        "payroll_runs",
        ["company_id", "period"],
    )


def downgrade():
    op.drop_constraint(
        "uq_payroll_runs_company_period",
        "payroll_runs",
        type_="unique",
    )
