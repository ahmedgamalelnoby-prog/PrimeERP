"""fix shipping pricing snapshot timestamp

Revision ID: 20260918_shipping_cost_timestamp
Revises: 20260918_shipping_financial_defaults
"""
from alembic import op
import sqlalchemy as sa

revision = "20260918_shipping_cost_timestamp"
down_revision = "20260918_shipping_financial_defaults"
branch_labels = None
depends_on = None

def upgrade():
    op.alter_column("shipping_shipment_costs", "calculated_at", existing_type=sa.Date(), type_=sa.DateTime(), existing_nullable=False)

def downgrade():
    op.alter_column("shipping_shipment_costs", "calculated_at", existing_type=sa.DateTime(), type_=sa.Date(), existing_nullable=False)
