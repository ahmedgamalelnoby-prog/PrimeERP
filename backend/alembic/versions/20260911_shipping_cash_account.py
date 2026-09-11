"""add dedicated cash account for shipping settlements

Revision ID: 20260911_shipping_cash_account
Revises: 20260911_tax_master_rbac
"""
from alembic import op
import sqlalchemy as sa

revision = "20260911_shipping_cash_account"
down_revision = "20260911_tax_master_rbac"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "shipping_carriers",
        sa.Column(
            "cash_account_id",
            sa.Integer(),
            sa.ForeignKey("account_combinations.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.create_index("ix_shipping_carriers_cash_account_id", "shipping_carriers", ["cash_account_id"])


def downgrade():
    op.drop_index("ix_shipping_carriers_cash_account_id", table_name="shipping_carriers")
    op.drop_column("shipping_carriers", "cash_account_id")
