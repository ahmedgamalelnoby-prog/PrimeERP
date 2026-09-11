"""add inventory items, branch warehouses and company central warehouse

Revision ID: 20260911warehouse
Revises: 20260831legal
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260911warehouse"
down_revision: Union[str, Sequence[str], None] = "20260831legal"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "inventory_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("sku", sa.String(length=80), nullable=False),
        sa.Column("barcode", sa.String(length=80), nullable=True),
        sa.Column("name_ar", sa.String(length=200), nullable=False),
        sa.Column("name_en", sa.String(length=200), nullable=True),
        sa.Column("item_type", sa.String(length=30), nullable=False, server_default="stockable"),
        sa.Column("uom", sa.String(length=30), nullable=False, server_default="unit"),
        sa.Column("costing_method", sa.String(length=20), nullable=False, server_default="weighted_average"),
        sa.Column("standard_cost", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("sales_price", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("purchase_price", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("reorder_level", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("company_id", "sku", name="uq_inventory_item_company_sku"),
        sa.UniqueConstraint("company_id", "barcode", name="uq_inventory_item_company_barcode"),
        sa.CheckConstraint("item_type IN ('stockable','consumable','service','non_stock')", name="ck_inventory_item_type"),
        sa.CheckConstraint("costing_method IN ('standard','weighted_average','fifo')", name="ck_inventory_item_costing_method"),
        sa.CheckConstraint("standard_cost >= 0", name="ck_inventory_item_standard_cost"),
        sa.CheckConstraint("sales_price >= 0", name="ck_inventory_item_sales_price"),
        sa.CheckConstraint("purchase_price >= 0", name="ck_inventory_item_purchase_price"),
        sa.CheckConstraint("reorder_level >= 0", name="ck_inventory_item_reorder_level"),
    )
    op.create_index("ix_inventory_items_company_id", "inventory_items", ["company_id"])
    op.create_index("ix_inventory_items_barcode", "inventory_items", ["barcode"])
    op.create_index("ix_inventory_items_category_id", "inventory_items", ["category_id"])

    op.create_table(
        "inventory_warehouses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=True),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_central", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("company_id", "code", name="uq_inventory_warehouse_company_code"),
        sa.CheckConstraint(
            "(is_central = true AND branch_id IS NULL) OR (is_central = false AND branch_id IS NOT NULL)",
            name="ck_inventory_warehouse_scope",
        ),
    )
    op.create_index("ix_inventory_warehouses_tenant_id", "inventory_warehouses", ["tenant_id"])
    op.create_index("ix_inventory_warehouses_company_id", "inventory_warehouses", ["company_id"])
    op.create_index("ix_inventory_warehouses_branch_id", "inventory_warehouses", ["branch_id"])
    op.create_index(
        "uq_inventory_warehouse_one_central",
        "inventory_warehouses",
        ["company_id"],
        unique=True,
        postgresql_where=sa.text("is_central = true"),
    )

    op.create_table(
        "inventory_stocks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("quantity_on_hand", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("quantity_reserved", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("average_cost", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["inventory_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["inventory_warehouses.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("company_id", "item_id", "warehouse_id", name="uq_inventory_stock_location"),
        sa.CheckConstraint("quantity_on_hand >= 0", name="ck_inventory_stock_on_hand"),
        sa.CheckConstraint("quantity_reserved >= 0", name="ck_inventory_stock_reserved"),
        sa.CheckConstraint("average_cost >= 0", name="ck_inventory_stock_average_cost"),
    )
    op.create_index("ix_inventory_stocks_company_id", "inventory_stocks", ["company_id"])
    op.create_index("ix_inventory_stocks_item_id", "inventory_stocks", ["item_id"])
    op.create_index("ix_inventory_stocks_warehouse_id", "inventory_stocks", ["warehouse_id"])


def downgrade() -> None:
    op.drop_table("inventory_stocks")
    op.drop_index("uq_inventory_warehouse_one_central", table_name="inventory_warehouses")
    op.drop_index("ix_inventory_warehouses_branch_id", table_name="inventory_warehouses")
    op.drop_index("ix_inventory_warehouses_company_id", table_name="inventory_warehouses")
    op.drop_index("ix_inventory_warehouses_tenant_id", table_name="inventory_warehouses")
    op.drop_table("inventory_warehouses")
    op.drop_index("ix_inventory_items_category_id", table_name="inventory_items")
    op.drop_index("ix_inventory_items_barcode", table_name="inventory_items")
    op.drop_index("ix_inventory_items_company_id", table_name="inventory_items")
    op.drop_table("inventory_items")
