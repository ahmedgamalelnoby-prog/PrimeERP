"""Harden enterprise module tenant/company integrity and business invariants.

Revision ID: 20260916_enterprise_module_integrity
Revises: 20260916_release_graph_final_merge
"""

from alembic import op
import sqlalchemy as sa

revision = "20260916_enterprise_module_integrity"
down_revision = "20260916_release_graph_final_merge"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

    # Enterprise tables currently carry company_id but not tenant_id. The
    # company FK is therefore the authoritative scope boundary; add composite
    # targets so child rows cannot point across companies.
    checks = [
        ("fixed_assets", "company_id", "companies", "id", "enterprise_asset_company"),
        ("employees", "company_id", "companies", "id", "enterprise_employee_company"),
        ("payroll_runs", "company_id", "companies", "id", "enterprise_payroll_company"),
        ("budgets", "company_id", "companies", "id", "enterprise_budget_company"),
        ("projects", "company_id", "companies", "id", "enterprise_project_company"),
        ("project_contracts", "company_id", "companies", "id", "enterprise_contract_company"),
    ]
    for table, col, parent, pcol, _ in checks:
        bind.execute(sa.text(f"SELECT 1 FROM {table} x LEFT JOIN {parent} p ON p.{pcol}=x.{col} WHERE p.{pcol} IS NULL LIMIT 1"))

    # Business invariants.
    op.create_check_constraint("ck_asset_depr_not_over_cost", "fixed_assets", "accumulated_depreciation >= 0 AND accumulated_depreciation <= cost - residual_value")
    op.create_check_constraint("ck_project_dates", "projects", "end_date IS NULL OR start_date IS NULL OR end_date >= start_date")
    op.create_check_constraint("ck_contract_dates", "project_contracts", "end_date IS NULL OR start_date IS NULL OR end_date >= start_date")
    op.create_check_constraint("ck_contract_retention", "project_contracts", "retention_percent >= 0 AND retention_percent <= 100")
    op.create_check_constraint("ck_payroll_totals", "payroll_runs", "total_gross >= 0 AND total_deductions >= 0 AND total_net >= 0 AND total_net = total_gross - total_deductions")
    op.create_check_constraint("ck_payroll_line_values", "payroll_lines", "gross >= 0 AND deductions >= 0 AND net = gross - deductions")
    op.create_check_constraint("ck_budget_line_period", "budget_lines", "period BETWEEN 1 AND 12")
    op.create_check_constraint("ck_budget_line_amount", "budget_lines", "amount >= 0 AND actual_amount >= 0")

    # Scope child rows to their parent company through composite foreign keys.
    op.create_unique_constraint("uq_budget_company_id", "budgets", ["company_id", "id"])
    op.create_unique_constraint("uq_project_company_id", "projects", ["company_id", "id"])
    op.create_unique_constraint("uq_payroll_run_company_id", "payroll_runs", ["company_id", "id"])
    op.create_unique_constraint("uq_employee_company_id", "employees", ["company_id", "id"])

    op.create_foreign_key("fk_budget_line_budget_company", "budget_lines", "budgets", ["budget_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_payroll_line_run", "payroll_lines", "payroll_runs", ["payroll_run_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_payroll_line_employee", "payroll_lines", "employees", ["employee_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_contract_project_company", "project_contracts", "projects", ["project_id"], ["id"], ondelete="CASCADE")

    # Business uniqueness within a company.
    op.create_unique_constraint("uq_asset_company_code", "fixed_assets", ["company_id", "code"])
    op.create_unique_constraint("uq_employee_company_no", "employees", ["company_id", "employee_no"])
    op.create_unique_constraint("uq_project_company_code", "projects", ["company_id", "code"])
    op.create_unique_constraint("uq_contract_company_no", "project_contracts", ["company_id", "contract_no"])
    op.create_unique_constraint("uq_payroll_company_period", "payroll_runs", ["company_id", "period"])
    op.create_unique_constraint("uq_budget_company_year_name", "budgets", ["company_id", "fiscal_year", "name"])
    op.create_unique_constraint("uq_budget_line_period_account", "budget_lines", ["budget_id", "account_id", "period"])


def downgrade():
    for name, table in [
        ("uq_budget_line_period_account", "budget_lines"),
        ("uq_budget_company_year_name", "budgets"),
        ("uq_payroll_company_period", "payroll_runs"),
        ("uq_contract_company_no", "project_contracts"),
        ("uq_project_company_code", "projects"),
        ("uq_employee_company_no", "employees"),
        ("uq_asset_company_code", "fixed_assets"),
        ("fk_contract_project_company", "project_contracts"),
        ("fk_payroll_line_employee", "payroll_lines"),
        ("fk_payroll_line_run", "payroll_lines"),
        ("fk_budget_line_budget_company", "budget_lines"),
        ("uq_employee_company_id", "employees"),
        ("uq_payroll_run_company_id", "payroll_runs"),
        ("uq_project_company_id", "projects"),
        ("uq_budget_company_id", "budgets"),
    ]:
        try:
            op.drop_constraint(name, table, type_="foreignkey" if name.startswith("fk_") else "unique")
        except Exception:
            pass
    for name, table in [
        ("ck_budget_line_amount", "budget_lines"),
        ("ck_budget_line_period", "budget_lines"),
        ("ck_payroll_line_values", "payroll_lines"),
        ("ck_payroll_totals", "payroll_runs"),
        ("ck_contract_retention", "project_contracts"),
        ("ck_contract_dates", "project_contracts"),
        ("ck_project_dates", "projects"),
        ("ck_asset_depr_not_over_cost", "fixed_assets"),
    ]:
        op.drop_constraint(name, table, type_="check")
