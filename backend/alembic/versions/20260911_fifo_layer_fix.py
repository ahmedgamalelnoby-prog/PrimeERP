"""allow multiple FIFO cost layers per receipt move

Revision ID: 20260911_fifo_layer_fix
Revises: 20260911_rbac_commerce
"""
from alembic import op

revision = "20260911_fifo_layer_fix"
down_revision = "20260911_rbac_commerce"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint(
        "uq_inventory_cost_layer_receipt_warehouse",
        "inventory_cost_layers",
        type_="unique",
    )


def downgrade():
    op.create_unique_constraint(
        "uq_inventory_cost_layer_receipt_warehouse",
        "inventory_cost_layers",
        ["receipt_move_id", "warehouse_id"],
    )
