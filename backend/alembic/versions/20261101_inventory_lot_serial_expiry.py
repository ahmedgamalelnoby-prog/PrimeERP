"""Add lot, serial, and expiry tracking controls to inventory.

Revision ID: 20261101_inventory_lot_serial_expiry
Revises: 20261031_below_cost_override_permission
"""
from alembic import op
import sqlalchemy as sa

revision = "20261101_inventory_lot_serial_expiry"
down_revision = "20261031_below_cost_override_permission"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("inventory_items", sa.Column("batch_tracking", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("inventory_items", sa.Column("serial_tracking", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("inventory_items", sa.Column("expiry_tracking", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("inventory_stock_moves", sa.Column("lot_number", sa.String(length=100), nullable=True))
    op.add_column("inventory_stock_moves", sa.Column("serial_number", sa.String(length=100), nullable=True))
    op.add_column("inventory_stock_moves", sa.Column("expiry_date", sa.Date(), nullable=True))
    op.create_index("ix_inventory_stock_moves_lot_number", "inventory_stock_moves", ["lot_number"])
    op.create_index("ix_inventory_stock_moves_serial_number", "inventory_stock_moves", ["serial_number"])
    op.create_index("ix_inventory_stock_moves_expiry_date", "inventory_stock_moves", ["expiry_date"])


def downgrade():
    op.drop_index("uq_inventory_stock_move_serial_identity", table_name="inventory_stock_moves")
    op.drop_index("ix_inventory_stock_moves_expiry_date", table_name="inventory_stock_moves")
    op.drop_index("ix_inventory_stock_moves_serial_number", table_name="inventory_stock_moves")
    op.drop_index("ix_inventory_stock_moves_lot_number", table_name="inventory_stock_moves")
    op.drop_column("inventory_stock_moves", "expiry_date")
    op.drop_column("inventory_stock_moves", "serial_number")
    op.drop_column("inventory_stock_moves", "lot_number")
    op.drop_column("inventory_items", "expiry_tracking")
    op.drop_column("inventory_items", "serial_tracking")
    op.drop_column("inventory_items", "batch_tracking")