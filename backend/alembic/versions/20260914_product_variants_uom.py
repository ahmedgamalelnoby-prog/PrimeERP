"""Add sales/purchase UOMs to inventory items.

Revision ID: 20260914_product_variants_uom
Revises: 20260914_product_variants
"""
from alembic import op
import sqlalchemy as sa

revision = "20260914_product_variants_uom"
down_revision = "20260914_product_variants"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("inventory_items", sa.Column("sales_uom_id", sa.Integer(), nullable=True))
    op.add_column("inventory_items", sa.Column("purchase_uom_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_inventory_items_sales_uom", "inventory_items", "units_of_measure",
        ["sales_uom_id"], ["id"], ondelete="RESTRICT"
    )
    op.create_foreign_key(
        "fk_inventory_items_purchase_uom", "inventory_items", "units_of_measure",
        ["purchase_uom_id"], ["id"], ondelete="RESTRICT"
    )
    op.create_index("ix_inventory_items_sales_uom_id", "inventory_items", ["sales_uom_id"])
    op.create_index("ix_inventory_items_purchase_uom_id", "inventory_items", ["purchase_uom_id"])


def downgrade():
    op.drop_index("ix_inventory_items_purchase_uom_id", table_name="inventory_items")
    op.drop_index("ix_inventory_items_sales_uom_id", table_name="inventory_items")
    op.drop_constraint("fk_inventory_items_purchase_uom", "inventory_items", type_="foreignkey")
    op.drop_constraint("fk_inventory_items_sales_uom", "inventory_items", type_="foreignkey")
    op.drop_column("inventory_items", "purchase_uom_id")
    op.drop_column("inventory_items", "sales_uom_id")
