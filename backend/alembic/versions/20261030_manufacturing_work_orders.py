"""Manufacturing work orders with WIP inventory movements.

Revision ID: 20261030_manufacturing_work_orders
Revises: 20261029_pos_cashier_shifts
"""
from alembic import op
import sqlalchemy as sa


revision = "20261030_manufacturing_work_orders"
down_revision = "20261029_pos_cashier_shifts"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "manufacturing_work_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("number", sa.String(60), nullable=False),
        sa.Column("recipe_id", sa.Integer(), sa.ForeignKey("recipes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("recipe_version", sa.Integer(), nullable=False),
        sa.Column("output_item_id", sa.Integer(), sa.ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("output_variant_id", sa.Integer(), sa.ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("source_location_id", sa.Integer(), sa.ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("destination_location_id", sa.Integer(), sa.ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("planned_quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("produced_quantity", sa.Numeric(18, 4), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="planned"),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("released_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("completed_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("company_id", "number", name="uq_manufacturing_work_order_company_number"),
        sa.CheckConstraint("recipe_version > 0", name="ck_manufacturing_work_order_recipe_version"),
        sa.CheckConstraint("planned_quantity > 0", name="ck_manufacturing_work_order_planned_qty"),
        sa.CheckConstraint("produced_quantity IS NULL OR produced_quantity > 0", name="ck_manufacturing_work_order_produced_qty"),
        sa.CheckConstraint("source_location_id <> destination_location_id", name="ck_manufacturing_work_order_locations"),
        sa.CheckConstraint("status IN ('planned','released','completed','cancelled')", name="ck_manufacturing_work_order_status"),
        sa.CheckConstraint(
            "(status IN ('planned','released','cancelled') AND produced_quantity IS NULL AND completed_at IS NULL) OR "
            "(status = 'completed' AND produced_quantity IS NOT NULL AND completed_at IS NOT NULL)",
            name="ck_manufacturing_work_order_completion",
        ),
    )
    op.create_index("ix_manufacturing_work_orders_company_id", "manufacturing_work_orders", ["company_id"])
    op.create_index("ix_manufacturing_work_orders_recipe_id", "manufacturing_work_orders", ["recipe_id"])
    op.create_index("ix_manufacturing_work_orders_output_item_id", "manufacturing_work_orders", ["output_item_id"])
    op.create_index("ix_manufacturing_work_orders_output_variant_id", "manufacturing_work_orders", ["output_variant_id"])
    op.create_index("ix_manufacturing_work_orders_source_location_id", "manufacturing_work_orders", ["source_location_id"])
    op.create_index("ix_manufacturing_work_orders_destination_location_id", "manufacturing_work_orders", ["destination_location_id"])
    op.create_index("ix_manufacturing_work_orders_status", "manufacturing_work_orders", ["status"])
    op.create_index("ix_manufacturing_work_order_company_status", "manufacturing_work_orders", ["company_id", "status"])

    op.create_table(
        "manufacturing_work_order_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("work_order_id", sa.Integer(), sa.ForeignKey("manufacturing_work_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_recipe_line_id", sa.Integer(), sa.ForeignKey("recipe_lines.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("ingredient_item_id", sa.Integer(), sa.ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity_per_output", sa.Numeric(18, 8), nullable=False),
        sa.Column("issued_quantity", sa.Numeric(18, 4), nullable=True),
        sa.Column("issue_move_id", sa.Integer(), sa.ForeignKey("inventory_stock_moves.id", ondelete="RESTRICT"), nullable=True),
        sa.UniqueConstraint("work_order_id", "source_recipe_line_id", name="uq_manufacturing_work_order_recipe_line"),
        sa.UniqueConstraint("issue_move_id", name="uq_manufacturing_work_order_line_issue_move"),
        sa.CheckConstraint("quantity_per_output > 0", name="ck_manufacturing_work_order_line_rate"),
        sa.CheckConstraint("issued_quantity IS NULL OR issued_quantity > 0", name="ck_manufacturing_work_order_line_issued_qty"),
    )
    op.create_index("ix_manufacturing_work_order_lines_work_order_id", "manufacturing_work_order_lines", ["work_order_id"])
    op.create_index("ix_manufacturing_work_order_lines_ingredient_item_id", "manufacturing_work_order_lines", ["ingredient_item_id"])

    op.drop_constraint("ck_inventory_stock_move_type", "inventory_stock_moves", type_="check")
    op.create_check_constraint(
        "ck_inventory_stock_move_type",
        "inventory_stock_moves",
        "movement_type IN ('receipt','issue','transfer','adjustment','opening','return','production_issue','production_receipt')",
    )


def downgrade():
    op.drop_constraint("ck_inventory_stock_move_type", "inventory_stock_moves", type_="check")
    op.create_check_constraint(
        "ck_inventory_stock_move_type",
        "inventory_stock_moves",
        "movement_type IN ('receipt','issue','transfer','adjustment','opening','return')",
    )
    op.drop_index("ix_manufacturing_work_order_lines_ingredient_item_id", table_name="manufacturing_work_order_lines")
    op.drop_index("ix_manufacturing_work_order_lines_work_order_id", table_name="manufacturing_work_order_lines")
    op.drop_table("manufacturing_work_order_lines")
    op.drop_index("ix_manufacturing_work_order_company_status", table_name="manufacturing_work_orders")
    op.drop_index("ix_manufacturing_work_orders_status", table_name="manufacturing_work_orders")
    op.drop_index("ix_manufacturing_work_orders_destination_location_id", table_name="manufacturing_work_orders")
    op.drop_index("ix_manufacturing_work_orders_source_location_id", table_name="manufacturing_work_orders")
    op.drop_index("ix_manufacturing_work_orders_output_variant_id", table_name="manufacturing_work_orders")
    op.drop_index("ix_manufacturing_work_orders_output_item_id", table_name="manufacturing_work_orders")
    op.drop_index("ix_manufacturing_work_orders_recipe_id", table_name="manufacturing_work_orders")
    op.drop_index("ix_manufacturing_work_orders_company_id", table_name="manufacturing_work_orders")
    op.drop_table("manufacturing_work_orders")
