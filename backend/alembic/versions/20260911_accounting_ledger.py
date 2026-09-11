"""add tax master

Revision ID: 20260911_accounting_ledger
Revises: 20260911enterprise
"""
from alembic import op
import sqlalchemy as sa

revision = "20260911_accounting_ledger"
down_revision = "20260911enterprise"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tax_rates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("rate", sa.Numeric(8, 4), nullable=False),
        sa.Column("tax_type", sa.String(20), nullable=False, server_default="vat"),
        sa.Column("is_withholding", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint("rate >= 0", name="ck_tax_rate_nonnegative"),
        sa.UniqueConstraint("company_id", "code", name="uq_tax_rates_company_code"),
    )
    op.create_index("ix_tax_rates_company_id", "tax_rates", ["company_id"])


def downgrade():
    op.drop_index("ix_tax_rates_company_id", table_name="tax_rates")
    op.drop_table("tax_rates")
