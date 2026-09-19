"""add carrier settlement fee breakdown

Revision ID: 20260918_shipping_settlement_fee_breakdown
Revises: 20260918_shipping_return_lifecycle
"""
from alembic import op
import sqlalchemy as sa

revision = "20260918_shipping_settlement_fee_breakdown"
down_revision = "20260918_shipping_return_lifecycle"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("shipping_shipment_settlements", sa.Column("cod_commission", sa.Numeric(18, 4), server_default="0", nullable=False))
    op.add_column("shipping_shipment_settlements", sa.Column("withdrawal_fee", sa.Numeric(18, 4), server_default="0", nullable=False))
    op.add_column("shipping_shipment_settlements", sa.Column("other_fee", sa.Numeric(18, 4), server_default="0", nullable=False))

def downgrade():
    op.drop_column("shipping_shipment_settlements", "other_fee")
    op.drop_column("shipping_shipment_settlements", "withdrawal_fee")
    op.drop_column("shipping_shipment_settlements", "cod_commission")
