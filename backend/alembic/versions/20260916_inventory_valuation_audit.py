"""Add inventory valuation allocation audit trail and reversal linkage.

Revision ID: 20260916_inventory_valuation_audit
Revises: 20260916_inventory_source_idempotency_fix
"""

from alembic import op
import sqlalchemy as sa

revision = "20260916_inventory_valuation_audit"
down_revision = "20260916_inventory_source_idempotency_fix"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "inventory_stock_moves",
        sa.Column("reversed_by_move_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_inventory_stock_moves_reversed_by_move_id",
        "inventory_stock_moves",
        ["reversed_by_move_id"],
    )
    op.create_foreign_key(
        "fk_inventory_stock_move_reversed_by",
        "inventory_stock_moves",
        "inventory_stock_moves",
        ["reversed_by_move_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.create_table(
        "inventory_valuation_allocations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("stock_move_id", sa.Integer(), nullable=False),
        sa.Column("cost_layer_id", sa.Integer(), nullable=True),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_cost", sa.Numeric(18, 4), nullable=False),
        sa.Column("allocation_role", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["stock_move_id"], ["inventory_stock_moves.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cost_layer_id"], ["inventory_cost_layers.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("quantity > 0", name="ck_inventory_valuation_allocation_quantity"),
        sa.CheckConstraint("unit_cost >= 0", name="ck_inventory_valuation_allocation_unit_cost"),
        sa.CheckConstraint("allocation_role IN ('source_consumed','destination_added')", name="ck_inventory_valuation_allocation_role"),
    )
    op.create_index("ix_inventory_valuation_allocations_company_id", "inventory_valuation_allocations", ["company_id"])
    op.create_index("ix_inventory_valuation_allocations_stock_move_id", "inventory_valuation_allocations", ["stock_move_id"])
    op.create_index("ix_inventory_valuation_allocations_cost_layer_id", "inventory_valuation_allocations", ["cost_layer_id"])


def downgrade():
    op.drop_index("ix_inventory_valuation_allocations_cost_layer_id", table_name="inventory_valuation_allocations")
    op.drop_index("ix_inventory_valuation_allocations_stock_move_id", table_name="inventory_valuation_allocations")
    op.drop_index("ix_inventory_valuation_allocations_company_id", table_name="inventory_valuation_allocations")
    op.drop_table("inventory_valuation_allocations")
    op.drop_constraint("fk_inventory_stock_move_reversed_by", "inventory_stock_moves", type_="foreignkey")
    op.drop_index("ix_inventory_stock_moves_reversed_by_move_id", table_name="inventory_stock_moves")
    op.drop_column("inventory_stock_moves", "reversed_by_move_id")
