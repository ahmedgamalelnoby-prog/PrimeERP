"""commerce accounting configuration

Revision ID: 20260911_commerce_accounting
Revises: 20260911_uom
"""
from alembic import op
import sqlalchemy as sa

revision = "20260911_commerce_accounting"
down_revision = "20260911_uom"
branch_labels = None

def upgrade():
    op.create_table(
        "commerce_accounting_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("sales_journal_id", sa.Integer(), sa.ForeignKey("accounting_journals.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("purchase_journal_id", sa.Integer(), sa.ForeignKey("accounting_journals.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("cash_journal_id", sa.Integer(), sa.ForeignKey("accounting_journals.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("ar_account_id", sa.Integer(), sa.ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("ap_account_id", sa.Integer(), sa.ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("sales_account_id", sa.Integer(), sa.ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("purchase_account_id", sa.Integer(), sa.ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("inventory_account_id", sa.Integer(), sa.ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("cogs_account_id", sa.Integer(), sa.ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("output_vat_account_id", sa.Integer(), sa.ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("input_vat_account_id", sa.Integer(), sa.ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("wht_account_id", sa.Integer(), sa.ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("default_branch_id", sa.Integer(), sa.ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("auto_post", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_commerce_accounting_settings_company", "commerce_accounting_settings", ["company_id"], unique=True)

def downgrade():
    op.drop_index("ix_commerce_accounting_settings_company", table_name="commerce_accounting_settings")
    op.drop_table("commerce_accounting_settings")
