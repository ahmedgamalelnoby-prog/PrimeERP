"""add inventory FIFO cost layers

Revision ID: 20260911_inventory_fifo_layers
Revises: 20260911_tax_rate_bounds
"""
from alembic import op
import sqlalchemy as sa

revision = "20260911_inventory_fifo_layers"
down_revision = "20260911_tax_rate_bounds"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "inventory_cost_layers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), sa.ForeignKey("inventory_warehouses.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("receipt_move_id", sa.Integer(), sa.ForeignKey("inventory_stock_moves.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity_remaining", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_cost", sa.Numeric(18, 4), nullable=False),
        sa.UniqueConstraint("receipt_move_id", "warehouse_id", name="uq_inventory_cost_layer_receipt_warehouse"),
        sa.CheckConstraint("quantity_remaining >= 0", name="ck_inventory_cost_layer_quantity"),
        sa.CheckConstraint("unit_cost >= 0", name="ck_inventory_cost_layer_unit_cost"),
    )
    op.create_index("ix_inventory_cost_layers_company_id", "inventory_cost_layers", ["company_id"])
    op.create_index("ix_inventory_cost_layers_item_id", "inventory_cost_layers", ["item_id"])
    op.create_index("ix_inventory_cost_layers_warehouse_id", "inventory_cost_layers", ["warehouse_id"])
    op.create_index("ix_inventory_cost_layers_receipt_move_id", "inventory_cost_layers", ["receipt_move_id"])


def downgrade():
    op.drop_index("ix_inventory_cost_layers_receipt_move_id", table_name="inventory_cost_layers")
    op.drop_index("ix_inventory_cost_layers_warehouse_id", table_name="inventory_cost_layers")
    op.drop_index("ix_inventory_cost_layers_item_id", table_name="inventory_cost_layers")
    op.drop_index("ix_inventory_cost_layers_company_id", table_name="inventory_cost_layers")
    op.drop_table("inventory_cost_layers")
