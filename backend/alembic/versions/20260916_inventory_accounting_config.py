"""Add inventory accounting configuration and transaction date.

Revision ID: 20260916_inventory_accounting_config
Revises: 20260916_inventory_transaction_integrity
"""

from alembic import op
import sqlalchemy as sa

revision = "20260916_inventory_accounting_config"
down_revision = "20260916_inventory_transaction_integrity"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "inventory_stock_moves",
        sa.Column("transaction_date", sa.Date(), nullable=True),
    )
    op.execute("UPDATE inventory_stock_moves SET transaction_date = CURRENT_DATE WHERE transaction_date IS NULL")
    op.alter_column("inventory_stock_moves", "transaction_date", nullable=False, server_default=sa.text("CURRENT_DATE"))
    op.create_index("ix_inventory_stock_moves_transaction_date", "inventory_stock_moves", ["transaction_date"])

    op.create_table(
        "inventory_accounting_configs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("journal_id", sa.Integer(), sa.ForeignKey("accounting_journals.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("branch_id", sa.Integer(), sa.ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("inventory_account_id", sa.Integer(), sa.ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("cogs_account_id", sa.Integer(), sa.ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("adjustment_account_id", sa.Integer(), sa.ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("clearing_account_id", sa.Integer(), sa.ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("is_active", sa.String(1), nullable=False, server_default="Y"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "company_id", name="uq_inventory_accounting_config_scope"),
        sa.CheckConstraint("is_active IN ('Y','N')", name="ck_inventory_accounting_config_active"),
    )
    op.create_index("ix_inventory_accounting_configs_tenant_id", "inventory_accounting_configs", ["tenant_id"])
    op.create_index("ix_inventory_accounting_configs_company_id", "inventory_accounting_configs", ["company_id"])


def downgrade():
    op.drop_index("ix_inventory_accounting_configs_company_id", table_name="inventory_accounting_configs")
    op.drop_index("ix_inventory_accounting_configs_tenant_id", table_name="inventory_accounting_configs")
    op.drop_table("inventory_accounting_configs")
    op.drop_index("ix_inventory_stock_moves_transaction_date", table_name="inventory_stock_moves")
    op.drop_column("inventory_stock_moves", "transaction_date")
