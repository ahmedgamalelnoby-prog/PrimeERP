"""Harden enterprise module business invariants.

Revision ID: 20260916_enterprise_module_integrity
Revises: 20260916_release_graph_final_merge
"""

from alembic import op
import sqlalchemy as sa

revision = "20260916_enterprise_module_integrity"
down_revision = "20260916_release_graph_final_merge"
branch_labels = None
depends_on = None


def _assert_clean(bind, sql: str, message: str) -> None:
    if bind.execute(sa.text(sql)).first() is not None:
        raise RuntimeError(message)


def _has_constraint(bind, table: str, name: str, types: tuple[str, ...] | None = None) -> bool:
    type_filter = ""
    params = {"table_name": table, "constraint_name": name}
    if types:
        type_filter = "AND c.contype = ANY(:constraint_types)"
        params["constraint_types"] = list(types)
    return bool(
        bind.execute(
            sa.text(
                f"""
                SELECT EXISTS (
                    SELECT 1
                    FROM pg_constraint c
                    JOIN pg_class t ON t.oid = c.conrelid
                    JOIN pg_namespace n ON n.oid = t.relnamespace
                    WHERE n.nspname = current_schema()
                      AND t.relname = :table_name
                      AND c.conname = :constraint_name
                      {type_filter}
                )
                """
            ),
            params,
        ).scalar()
    )


def _has_unique_key(bind, table: str, columns: list[str]) -> bool:
    """Return True when an exact usable unique constraint/index already exists."""
    result = bind.execute(
        sa.text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM pg_constraint c
                JOIN pg_class t ON t.oid = c.conrelid
                JOIN pg_namespace n ON n.oid = t.relnamespace
                WHERE n.nspname = current_schema()
                  AND t.relname = :table_name
                  AND c.contype IN ('p', 'u')
                  AND (
                      SELECT array_agg(a.attname::text ORDER BY k.ord)
                      FROM unnest(c.conkey) WITH ORDINALITY AS k(attnum, ord)
                      JOIN pg_attribute a
                        ON a.attrelid = t.oid
                       AND a.attnum = k.attnum
                  ) = CAST(:columns AS text[])
            )
            OR EXISTS (
                SELECT 1
                FROM pg_index i
                JOIN pg_class t ON t.oid = i.indrelid
                JOIN pg_namespace n ON n.oid = t.relnamespace
                WHERE n.nspname = current_schema()
                  AND t.relname = :table_name
                  AND i.indisunique
                  AND i.indisvalid
                  AND i.indpred IS NULL
                  AND (
                      SELECT array_agg(a.attname::text ORDER BY k.ord)
                      FROM unnest(i.indkey) WITH ORDINALITY AS k(attnum, ord)
                      JOIN pg_attribute a
                        ON a.attrelid = t.oid
                       AND a.attnum = k.attnum
                  ) = CAST(:columns AS text[])
            )
            """
        ),
        {"table_name": table, "columns": "{" + ",".join(columns) + "}"},
    )
    return bool(result.scalar())


def _relation_name_exists(bind, name: str) -> bool:
    return bool(
        bind.execute(
            sa.text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE n.nspname = current_schema()
                      AND c.relname = :name
                )
                OR EXISTS (
                    SELECT 1
                    FROM pg_constraint c
                    JOIN pg_class t ON t.oid = c.conrelid
                    JOIN pg_namespace n ON n.oid = t.relnamespace
                    WHERE n.nspname = current_schema()
                      AND c.conname = :name
                )
                """
            ),
            {"name": name},
        ).scalar()
    )


def _ensure_check_constraint(bind, name: str, table: str, condition: str) -> None:
    if not _has_constraint(bind, table, name, ("c",)):
        op.create_check_constraint(name, table, condition)


def _ensure_unique_constraint(bind, name: str, table: str, columns: list[str]) -> None:
    if _has_unique_key(bind, table, columns):
        return
    if _relation_name_exists(bind, name):
        raise RuntimeError(
            f"Cannot create required unique key {name} on {table}: an incompatible relation or constraint with that name already exists."
        )
    op.create_unique_constraint(name, table, columns)


def upgrade():
    bind = op.get_bind()

    _assert_clean(bind, "SELECT 1 FROM fixed_assets WHERE residual_value > cost OR accumulated_depreciation < 0 OR accumulated_depreciation > cost - residual_value LIMIT 1", "Cannot harden fixed assets: invalid depreciation state exists")
    _assert_clean(bind, "SELECT 1 FROM projects WHERE end_date IS NOT NULL AND start_date IS NOT NULL AND end_date < start_date LIMIT 1", "Cannot harden projects: invalid date range exists")
    _assert_clean(bind, "SELECT 1 FROM project_contracts WHERE end_date IS NOT NULL AND start_date IS NOT NULL AND end_date < start_date LIMIT 1", "Cannot harden project contracts: invalid date range exists")
    _assert_clean(bind, "SELECT 1 FROM payroll_runs WHERE total_gross < 0 OR total_deductions < 0 OR total_net < 0 OR total_net <> total_gross - total_deductions LIMIT 1", "Cannot harden payroll: invalid run totals exist")
    _assert_clean(bind, "SELECT 1 FROM payroll_lines WHERE gross < 0 OR deductions < 0 OR net <> gross - deductions LIMIT 1", "Cannot harden payroll: invalid line totals exist")
    _assert_clean(bind, "SELECT 1 FROM budget_lines WHERE period < 1 OR period > 12 OR amount < 0 OR actual_amount < 0 LIMIT 1", "Cannot harden budgets: invalid line exists")

    for table, column, parent in [
        ("fixed_assets", "company_id", "companies"),
        ("employees", "company_id", "companies"),
        ("payroll_runs", "company_id", "companies"),
        ("budgets", "company_id", "companies"),
        ("projects", "company_id", "companies"),
        ("project_contracts", "company_id", "companies"),
    ]:
        _assert_clean(bind, f"SELECT 1 FROM {table} x LEFT JOIN {parent} p ON p.id=x.{column} WHERE p.id IS NULL LIMIT 1", f"Cannot harden {table}: orphan company reference exists")

    _ensure_check_constraint(bind, "ck_asset_depr_not_over_cost", "fixed_assets", "residual_value <= cost AND accumulated_depreciation >= 0 AND accumulated_depreciation <= cost - residual_value")
    _ensure_check_constraint(bind, "ck_project_dates", "projects", "end_date IS NULL OR start_date IS NULL OR end_date >= start_date")
    _ensure_check_constraint(bind, "ck_contract_dates", "project_contracts", "end_date IS NULL OR start_date IS NULL OR end_date >= start_date")
    _ensure_check_constraint(bind, "ck_contract_retention", "project_contracts", "retention_percent >= 0 AND retention_percent <= 100")
    _ensure_check_constraint(bind, "ck_payroll_totals", "payroll_runs", "total_gross >= 0 AND total_deductions >= 0 AND total_net >= 0 AND total_net = total_gross - total_deductions")
    _ensure_check_constraint(bind, "ck_payroll_line_values", "payroll_lines", "gross >= 0 AND deductions >= 0 AND net = gross - deductions")
    _ensure_check_constraint(bind, "ck_budget_line_period", "budget_lines", "period BETWEEN 1 AND 12")
    _ensure_check_constraint(bind, "ck_budget_line_amount", "budget_lines", "amount >= 0 AND actual_amount >= 0")

    _ensure_unique_constraint(bind, "uq_asset_company_code", "fixed_assets", ["company_id", "code"])
    _ensure_unique_constraint(bind, "uq_employee_company_no", "employees", ["company_id", "employee_no"])
    _ensure_unique_constraint(bind, "uq_project_company_code", "projects", ["company_id", "code"])
    _ensure_unique_constraint(bind, "uq_contract_company_no", "project_contracts", ["company_id", "contract_no"])
    _ensure_unique_constraint(bind, "uq_payroll_company_period", "payroll_runs", ["company_id", "period"])
    _ensure_unique_constraint(bind, "uq_budget_company_year_name", "budgets", ["company_id", "fiscal_year", "name"])
    _ensure_unique_constraint(bind, "uq_budget_line_period_account", "budget_lines", ["budget_id", "account_id", "period"])


def downgrade():
    for name, table in [
        ("uq_budget_line_period_account", "budget_lines"),
        ("uq_budget_company_year_name", "budgets"),
        ("uq_payroll_company_period", "payroll_runs"),
        ("uq_contract_company_no", "project_contracts"),
        ("uq_project_company_code", "projects"),
        ("uq_employee_company_no", "employees"),
        ("uq_asset_company_code", "fixed_assets"),
    ]:
        op.drop_constraint(name, table, type_="unique")
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
