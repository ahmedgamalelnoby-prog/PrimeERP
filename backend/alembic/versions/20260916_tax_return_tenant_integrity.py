"""Harden tax return drafts with tenant ownership.

Revision ID: 20260916_tax_return_tenant_integrity
Revises: 20260915_journal_company_tenant_integrity
"""
from alembic import op
import sqlalchemy as sa

revision = "20260916_tax_return_tenant_integrity"
down_revision = "20260915_journal_company_tenant_integrity"
branch_labels = None
depends_on = None


def _assert_clean(conn, sql: str, message: str) -> None:
    if conn.execute(sa.text(sql)).scalar():
        raise RuntimeError(message)


def upgrade():
    conn = op.get_bind()

    op.add_column("tax_return_drafts", sa.Column("tenant_id", sa.Integer(), nullable=True))

    conn.execute(sa.text("""
        UPDATE tax_return_drafts tr
        SET tenant_id = c.tenant_id
        FROM companies c
        WHERE c.id = tr.company_id
    """))

    _assert_clean(
        conn,
        "SELECT EXISTS (SELECT 1 FROM tax_return_drafts WHERE tenant_id IS NULL)",
        "Cannot harden tax_return_drafts: company ownership could not be resolved.",
    )

    _assert_clean(
        conn,
        "SELECT EXISTS (SELECT 1 FROM tax_return_drafts tr JOIN companies c ON c.id = tr.company_id WHERE tr.tenant_id <> c.tenant_id)",
        "Cannot harden tax_return_drafts: tenant does not match company tenant.",
    )

    op.alter_column("tax_return_drafts", "tenant_id", nullable=False)
    op.create_unique_constraint("uq_companies_tenant_id_tax_return", "companies", ["tenant_id", "id"])
    op.create_foreign_key(
        "fk_tax_return_draft_company_same_tenant",
        "tax_return_drafts",
        "companies",
        ["tenant_id", "company_id"],
        ["tenant_id", "id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_tax_return_drafts_tenant_company", "tax_return_drafts", ["tenant_id", "company_id"])


def downgrade():
    op.drop_index("ix_tax_return_drafts_tenant_company", table_name="tax_return_drafts")
    op.drop_constraint("fk_tax_return_draft_company_same_tenant", "tax_return_drafts", type_="foreignkey")
    op.drop_constraint("uq_companies_tenant_id_tax_return", "companies", type_="unique")
    op.drop_column("tax_return_drafts", "tenant_id")
