"""Enforce tenant ownership of accounting journals and entries.

Revision ID: 20260915_journal_company_tenant_integrity
Revises: 20260915_journal_scope_integrity
"""
from alembic import op
import sqlalchemy as sa

revision = "20260915_journal_company_tenant_integrity"
down_revision = "20260915_journal_scope_integrity"
branch_labels = None
depends_on = None


def _assert_clean(conn, sql: str, message: str) -> None:
    if conn.execute(sa.text(sql)).scalar():
        raise RuntimeError(message)


def upgrade():
    conn = op.get_bind()

    _assert_clean(
        conn,
        "SELECT EXISTS (SELECT 1 FROM accounting_journals j JOIN companies c ON c.id = j.company_id WHERE j.tenant_id <> c.tenant_id)",
        "Cannot harden accounting_journals: journal company belongs to another tenant.",
    )
    _assert_clean(
        conn,
        "SELECT EXISTS (SELECT 1 FROM journal_entries e JOIN companies c ON c.id = e.company_id WHERE e.tenant_id <> c.tenant_id)",
        "Cannot harden journal_entries: entry company belongs to another tenant.",
    )
    _assert_clean(
        conn,
        "SELECT EXISTS (SELECT 1 FROM journal_entries e JOIN accounting_journals j ON j.id = e.journal_id WHERE e.tenant_id <> j.tenant_id OR e.company_id <> j.company_id)",
        "Cannot harden journal_entries: entry references a journal from another tenant/company.",
    )

    op.create_unique_constraint("uq_companies_tenant_id_journal", "companies", ["tenant_id", "id"])
    op.create_unique_constraint("uq_accounting_journals_tenant_company_id", "accounting_journals", ["tenant_id", "company_id", "id"])

    op.create_foreign_key(
        "fk_accounting_journal_company_same_tenant",
        "accounting_journals",
        "companies",
        ["tenant_id", "company_id"],
        ["tenant_id", "id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_journal_entry_company_same_tenant",
        "journal_entries",
        "companies",
        ["tenant_id", "company_id"],
        ["tenant_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_journal_entry_journal_same_scope",
        "journal_entries",
        "accounting_journals",
        ["tenant_id", "company_id", "journal_id"],
        ["tenant_id", "company_id", "id"],
        ondelete="RESTRICT",
    )


def downgrade():
    op.drop_constraint("fk_journal_entry_journal_same_scope", "journal_entries", type_="foreignkey")
    op.drop_constraint("fk_journal_entry_company_same_tenant", "journal_entries", type_="foreignkey")
    op.drop_constraint("fk_accounting_journal_company_same_tenant", "accounting_journals", type_="foreignkey")
    op.drop_constraint("uq_accounting_journals_tenant_company_id", "accounting_journals", type_="unique")
    op.drop_constraint("uq_companies_tenant_id_journal", "companies", type_="unique")
