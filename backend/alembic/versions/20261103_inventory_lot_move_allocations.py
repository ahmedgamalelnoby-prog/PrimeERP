"""Audit per-lot quantities consumed and received by stock movements.

Revision ID: 20261103_inventory_lot_move_allocations
Revises: 20261102_inventory_lot_balances
"""
from alembic import op
import sqlalchemy as sa

revision = "20261103_inventory_lot_move_allocations"
down_revision = "20261102_inventory_lot_balances"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "inventory_lot_move_allocations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stock_move_id", sa.Integer(), sa.ForeignKey("inventory_stock_moves.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lot_number", sa.String(length=100), nullable=True),
        sa.Column("serial_number", sa.String(length=100), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("quantity > 0", name="ck_inventory_lot_move_allocation_quantity"),
        sa.CheckConstraint("lot_number IS NOT NULL OR serial_number IS NOT NULL", name="ck_inventory_lot_move_allocation_identity"),
    )
    op.create_index("ix_inventory_lot_move_allocations_id", "inventory_lot_move_allocations", ["id"])
    op.create_index("ix_inventory_lot_move_allocations_company_id", "inventory_lot_move_allocations", ["company_id"])
    op.create_index("ix_inventory_lot_move_allocations_stock_move_id", "inventory_lot_move_allocations", ["stock_move_id"])


def downgrade():
    op.drop_index("ix_inventory_lot_move_allocations_id", table_name="inventory_lot_move_allocations")
    op.drop_index("ix_inventory_lot_move_allocations_stock_move_id", table_name="inventory_lot_move_allocations")
    op.drop_index("ix_inventory_lot_move_allocations_company_id", table_name="inventory_lot_move_allocations")
    op.drop_table("inventory_lot_move_allocations")
