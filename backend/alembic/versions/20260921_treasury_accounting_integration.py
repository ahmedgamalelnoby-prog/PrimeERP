"""add treasury accounting configuration.

Revision ID: 20260921_treasury_accounting_integration
Revises: 20260921_purchasing_treasury_rbac
"""
from alembic import op
import sqlalchemy as sa

revision = "20260921_treasury_accounting_integration"
down_revision = "20260921_purchasing_treasury_rbac"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "treasury_accounting_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("journal_id", sa.Integer(), sa.ForeignKey("accounting_journals.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("default_branch_id", sa.Integer(), sa.ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("received_cheques_account_id", sa.Integer(), sa.ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("under_collection_account_id", sa.Integer(), sa.ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("returned_cheques_account_id", sa.Integer(), sa.ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("issued_cheques_account_id", sa.Integer(), sa.ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("bank_account_id", sa.Integer(), sa.ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("auto_post", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("company_id", name="uq_treasury_accounting_settings_company"),
    )
    op.create_index("ix_treasury_accounting_settings_company_id", "treasury_accounting_settings", ["company_id"], unique=True)


def downgrade():
    op.drop_index("ix_treasury_accounting_settings_company_id", table_name="treasury_accounting_settings")
    op.drop_table("treasury_accounting_settings")
