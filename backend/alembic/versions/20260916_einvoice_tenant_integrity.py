"""Enforce tenant ownership of Egyptian e-invoice documents.

Revision ID: 20260916_einvoice_tenant_integrity
Revises: 20260915_journal_company_tenant_integrity
"""
from alembic import op
import sqlalchemy as sa

revision = "20260916_einvoice_tenant_integrity"
down_revision = "20260915_journal_company_tenant_integrity"
branch_labels = None
depends_on = None


def _assert_clean(conn, sql: str, message: str) -> None:
    if conn.execute(sa.text(sql)).scalar():
        raise RuntimeError(message)


def upgrade():
    conn = op.get_bind()
    op.add_column("egyptian_einvoice_documents", sa.Column("tenant_id", sa.Integer(), nullable=True))

    conn.execute(sa.text(
        "UPDATE egyptian_einvoice_documents d "
        "SET tenant_id = c.tenant_id "
        "FROM companies c WHERE c.id = d.company_id"
    ))

    _assert_clean(
        conn,
        "SELECT EXISTS (SELECT 1 FROM egyptian_einvoice_documents WHERE tenant_id IS NULL)",
        "Cannot harden Egyptian e-invoices: one or more documents reference a company without a tenant.",
    )

    op.alter_column("egyptian_einvoice_documents", "tenant_id", nullable=False)
    op.create_unique_constraint(
        "uq_eta_document_tenant_company_id",
        "egyptian_einvoice_documents",
        ["tenant_id", "company_id", "id"],
    )
    op.create_foreign_key(
        "fk_eta_document_company_same_tenant",
        "egyptian_einvoice_documents",
        "companies",
        ["tenant_id", "company_id"],
        ["tenant_id", "id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_eta_documents_tenant_id", "egyptian_einvoice_documents", ["tenant_id"])


def downgrade():
    op.drop_index("ix_eta_documents_tenant_id", table_name="egyptian_einvoice_documents")
    op.drop_constraint("fk_eta_document_company_same_tenant", "egyptian_einvoice_documents", type_="foreignkey")
    op.drop_constraint("uq_eta_document_tenant_company_id", "egyptian_einvoice_documents", type_="unique")
    op.drop_column("egyptian_einvoice_documents", "tenant_id")
