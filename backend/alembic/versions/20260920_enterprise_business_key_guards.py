"""Enforce company-scoped enterprise business-key uniqueness.

Revision ID: 20260920_enterprise_business_key_guards
Revises: 20260920_release_gate_merge
"""
from alembic import op

revision = "20260920_enterprise_business_key_guards"
down_revision = "20260920_release_gate_merge"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint("uq_fixed_assets_company_code", "fixed_assets", ["company_id", "code"])
    op.create_unique_constraint("uq_budgets_company_name_year", "budgets", ["company_id", "name", "fiscal_year"])
    op.create_unique_constraint("uq_budget_lines_budget_account_period", "budget_lines", ["budget_id", "account_id", "period"])
    op.create_unique_constraint("uq_employees_company_employee_no", "employees", ["company_id", "employee_no"])
    op.create_unique_constraint("uq_projects_company_code", "projects", ["company_id", "code"])
    op.create_unique_constraint("uq_project_contracts_company_contract_no", "project_contracts", ["company_id", "contract_no"])


def downgrade():
    op.drop_constraint("uq_project_contracts_company_contract_no", "project_contracts", type_="unique")
    op.drop_constraint("uq_projects_company_code", "projects", type_="unique")
    op.drop_constraint("uq_employees_company_employee_no", "employees", type_="unique")
    op.drop_constraint("uq_budget_lines_budget_account_period", "budget_lines", type_="unique")
    op.drop_constraint("uq_budgets_company_name_year", "budgets", type_="unique")
    op.drop_constraint("uq_fixed_assets_company_code", "fixed_assets", type_="unique")
