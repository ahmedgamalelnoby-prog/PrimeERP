"""immutable tax/legal transaction snapshots

Revision ID: 20260914_tax_snapshots
Revises: 20260914_global_jurisdiction
"""
from alembic import op
import sqlalchemy as sa

revision = "20260914_tax_snapshots"
down_revision = "20260914_global_jurisdiction"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("tax_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_kind", sa.String(20), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("decision_id", sa.Integer(), sa.ForeignKey("jurisdiction_decisions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("jurisdiction_code", sa.String(20), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("transaction_type", sa.String(40), nullable=False),
        sa.Column("place_of_supply", sa.String(30), nullable=False),
        sa.Column("b2b", sa.Boolean(), nullable=False),
        sa.Column("facts", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("rules", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("document_kind IN ('sale','purchase','payment','credit_note','debit_note')", name="ck_tax_snapshot_document_kind"),
        sa.UniqueConstraint("company_id", "document_kind", "document_id", name="uq_tax_snapshot_document"),
    )
    op.create_index("ix_tax_snapshots_company_id", "tax_snapshots", ["company_id"])
    op.create_index("ix_tax_snapshots_document", "tax_snapshots", ["document_kind", "document_id"])
    op.create_index("ix_tax_snapshots_decision_id", "tax_snapshots", ["decision_id"])


def downgrade():
    op.drop_table("tax_snapshots")
