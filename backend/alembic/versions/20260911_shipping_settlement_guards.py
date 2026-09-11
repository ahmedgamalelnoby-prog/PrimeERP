"""add shipping settlement financial guards

Revision ID: 20260911_shipping_settlement_guards
Revises: e01d1a2725a2487d82826e1cf22d15c2cf63000b
"""
from alembic import op

revision = "20260911_shipping_settlement_guards"
down_revision = "20260911_shipping_cash_account"
branch_labels = None
depends_on = None


def upgrade():
    op.create_check_constraint(
        "ck_shipping_ship_settle_fee_not_over_collected",
        "shipping_shipment_settlements",
        "carrier_fee <= collected_amount",
    )


def downgrade():
    op.drop_constraint(
        "ck_shipping_ship_settle_fee_not_over_collected",
        "shipping_shipment_settlements",
        type_="check",
    )
