"""add shipping settlement accounting accounts

Revision ID: 20260911_shipping_accounting
Revises: 20260911_journal_source_guard
"""
from alembic import op
import sqlalchemy as sa

revision = "20260911_shipping_accounting"
down_revision = "20260911_journal_source_guard"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("shipping_carriers", sa.Column("settlement_account_id", sa.Integer(), nullable=True))
    op.add_column("shipping_carriers", sa.Column("fee_account_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_shipping_carrier_settlement_account",
        "shipping_carriers", "account_combinations",
        ["settlement_account_id"], ["id"], ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_shipping_carrier_fee_account",
        "shipping_carriers", "account_combinations",
        ["fee_account_id"], ["id"], ondelete="RESTRICT",
    )
    op.create_index("ix_shipping_carrier_settlement_account", "shipping_carriers", ["settlement_account_id"])
    op.create_index("ix_shipping_carrier_fee_account", "shipping_carriers", ["fee_account_id"])


def downgrade():
    op.drop_index("ix_shipping_carrier_fee_account", table_name="shipping_carriers")
    op.drop_index("ix_shipping_carrier_settlement_account", table_name="shipping_carriers")
    op.drop_constraint("fk_shipping_carrier_fee_account", "shipping_carriers", type_="foreignkey")
    op.drop_constraint("fk_shipping_carrier_settlement_account", "shipping_carriers", type_="foreignkey")
    op.drop_column("shipping_carriers", "fee_account_id")
    op.drop_column("shipping_carriers", "settlement_account_id")
