"""tax return draft and reconciliation workflow

Revision ID: 20260915_tax_return_drafts
Revises: 20260915_einvoice_idempotency
"""
from alembic import op
import sqlalchemy as sa

revision = "20260915_tax_return_drafts"
down_revision = "20260915_einvoice_idempotency"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tax_return_drafts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("jurisdiction_code", sa.String(30), nullable=False, server_default="EG"),
        sa.Column("period_from", sa.Date(), nullable=False),
        sa.Column("period_to", sa.Date(), nullable=False),
        sa.Column("output_vat", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("input_vat", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("adjustments", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("wht_payable", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("net_vat", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("reconciliation_difference", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("is_reconciled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("submission_reference", sa.String(255)),
        sa.Column("submission_status", sa.String(30), nullable=False, server_default="not_supported"),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("period_to >= period_from", name="ck_tax_return_period"),
        sa.CheckConstraint("status IN ('draft','review','approved','closed')", name="ck_tax_return_status"),
    )
    op.create_index("ix_tax_return_drafts_company_id", "tax_return_drafts", ["company_id"])
    op.create_index("ix_tax_return_drafts_status", "tax_return_drafts", ["status"])
    op.create_unique_constraint("uq_tax_return_draft_period", "tax_return_drafts", ["company_id", "jurisdiction_code", "period_from", "period_to"])


def downgrade():
    op.drop_table("tax_return_drafts")
