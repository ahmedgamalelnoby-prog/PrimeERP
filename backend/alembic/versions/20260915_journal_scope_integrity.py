"""Enforce tenant/company scope on journal entry lines.

Revision ID: 20260915_journal_scope_integrity
Revises: 20260915_tax_rate_domain_hardening
"""
from alembic import op
import sqlalchemy as sa

revision = "20260915_journal_scope_integrity"
down_revision = "20260915_tax_rate_domain_hardening"
branch_labels = None
depends_on = None


def _assert_clean(conn, sql: str, message: str) -> None:
    if conn.execute(sa.text(sql)).scalar():
        raise RuntimeError(message)


def upgrade():
    conn = op.get_bind()

    _assert_clean(
        conn,
        "SELECT EXISTS (SELECT 1 FROM journal_entry_lines l JOIN journal_entries e ON e.id = l.entry_id WHERE l.tenant_id <> e.tenant_id)",
        "Cannot harden journal_entry_lines: tenant scope does not match parent entry.",
    )
    _assert_clean(
        conn,
        "SELECT EXISTS (SELECT 1 FROM journal_entry_lines l JOIN journal_entries e ON e.id = l.entry_id JOIN account_combinations a ON a.id = l.account_combination_id WHERE e.company_id <> a.company_id)",
        "Cannot harden journal_entry_lines: account combination belongs to another company.",
    )
    _assert_clean(
        conn,
        "SELECT EXISTS (SELECT 1 FROM journal_entry_lines l JOIN journal_entries e ON e.id = l.entry_id JOIN accounting_departments d ON d.id = l.department_id WHERE l.department_id IS NOT NULL AND e.company_id <> d.company_id)",
        "Cannot harden journal_entry_lines: department belongs to another company.",
    )
    _assert_clean(
        conn,
        "SELECT EXISTS (SELECT 1 FROM journal_entry_lines l JOIN journal_entries e ON e.id = l.entry_id JOIN accounting_cost_centers c ON c.id = l.cost_center_id WHERE l.cost_center_id IS NOT NULL AND e.company_id <> c.company_id)",
        "Cannot harden journal_entry_lines: cost center belongs to another company.",
    )

    op.add_column("journal_entry_lines", sa.Column("company_id", sa.Integer(), nullable=True))
    conn.execute(sa.text("UPDATE journal_entry_lines l SET company_id = e.company_id FROM journal_entries e WHERE e.id = l.entry_id"))
    _assert_clean(conn, "SELECT EXISTS (SELECT 1 FROM journal_entry_lines WHERE company_id IS NULL)", "Cannot harden journal_entry_lines: company could not be derived from parent entry.")
    op.alter_column("journal_entry_lines", "company_id", nullable=False)
    op.create_index("ix_journal_line_company_entry", "journal_entry_lines", ["company_id", "entry_id"])

    op.create_unique_constraint("uq_journal_entries_tenant_company_id", "journal_entries", ["tenant_id", "company_id", "id"])
    op.create_unique_constraint("uq_account_combinations_company_id", "account_combinations", ["company_id", "id"])

    op.create_foreign_key(
        "fk_journal_line_entry_same_scope",
        "journal_entry_lines",
        "journal_entries",
        ["tenant_id", "company_id", "entry_id"],
        ["tenant_id", "company_id", "id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_journal_line_account_same_company",
        "journal_entry_lines",
        "account_combinations",
        ["company_id", "account_combination_id"],
        ["company_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_journal_line_department_same_company",
        "journal_entry_lines",
        "accounting_departments",
        ["company_id", "department_id"],
        ["company_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_journal_line_cost_center_same_company",
        "journal_entry_lines",
        "accounting_cost_centers",
        ["company_id", "cost_center_id"],
        ["company_id", "id"],
        ondelete="RESTRICT",
    )

    op.create_check_constraint(
        "ck_journal_line_base_amounts_nonnegative",
        "journal_entry_lines",
        "base_debit >= 0 AND base_credit >= 0",
    )


def downgrade():
    op.drop_constraint("ck_journal_line_base_amounts_nonnegative", "journal_entry_lines", type_="check")
    op.drop_constraint("fk_journal_line_cost_center_same_company", "journal_entry_lines", type_="foreignkey")
    op.drop_constraint("fk_journal_line_department_same_company", "journal_entry_lines", type_="foreignkey")
    op.drop_constraint("fk_journal_line_account_same_company", "journal_entry_lines", type_="foreignkey")
    op.drop_constraint("fk_journal_line_entry_same_scope", "journal_entry_lines", type_="foreignkey")
    op.drop_constraint("uq_account_combinations_company_id", "account_combinations", type_="unique")
    op.drop_constraint("uq_journal_entries_tenant_company_id", "journal_entries", type_="unique")
    op.drop_index("ix_journal_line_company_entry", table_name="journal_entry_lines")
    op.drop_column("journal_entry_lines", "company_id")
