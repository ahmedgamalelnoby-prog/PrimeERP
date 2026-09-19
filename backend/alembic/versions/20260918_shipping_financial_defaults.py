"""harden default shipping financial actions

Revision ID: 20260918_shipping_financial_defaults
Revises: 20260918_shipping_settlement_fee_breakdown
"""
from alembic import op

revision = "20260918_shipping_financial_defaults"
down_revision = "20260918_shipping_settlement_fee_breakdown"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "UPDATE shipping_order_statuses "
        "SET financial_actions='["recognize_revenue", "recognize_shipping_revenue", "
        ""recognize_shipping_cost", "create_cod_receivable", "recognize_cod_fee"]' "
        "WHERE code='delivered' AND financial_actions='["recognize_revenue", "recognize_shipping_revenue", "
        ""recognize_shipping_cost", "create_cod_receivable", "recognize_cod_fee", "recognize_card_fee"]'"
    )


def downgrade():
    op.execute(
        "UPDATE shipping_order_statuses "
        "SET financial_actions='["recognize_revenue", "recognize_shipping_revenue", "
        ""recognize_shipping_cost", "create_cod_receivable", "recognize_cod_fee", "recognize_card_fee"]' "
        "WHERE code='delivered' AND financial_actions='["recognize_revenue", "recognize_shipping_revenue", "
        ""recognize_shipping_cost", "create_cod_receivable", "recognize_cod_fee"]'"
    )
