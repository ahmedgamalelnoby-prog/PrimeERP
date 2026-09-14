"""Add product variants, multiple barcodes and sales/purchase UOMs.

Revision ID: 20260914_product_variants_uom
Revises: 20260914_recipe_uom_snapshot
"""
from alembic import op
import sqlalchemy as sa

revision = "20260914_product_variants_uom"
down_revision = "20260914_recipe_uom_snapshot"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("inventory_items", sa.Column("sales_uom_id", sa.Integer(), nullable=True))
    op.add_column("inventory_items", sa.Column("purchase_uom_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_inventory_items_sales_uom", "inventory_items", "units_of_measure", ["sales_uom_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_inventory_items_purchase_uom", "inventory_items", "units_of_measure", ["purchase_uom_id"], ["id"], ondelete="RESTRICT")
    op.create_index("ix_inventory_items_sales_uom_id", "inventory_items", ["sales_uom_id"])
    op.create_index("ix_inventory_items_purchase_uom_id", "inventory_items", ["purchase_uom_id"])

    op.create_table(
        "product_variants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sku", sa.String(100), nullable=False),
        sa.Column("name_ar", sa.String(200), nullable=False),
        sa.Column("name_en", sa.String(200)),
        sa.Column("attributes", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("uom_id", sa.Integer(), sa.ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("sales_price", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("purchase_price", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "sku", name="uq_product_variant_company_sku"),
        sa.CheckConstraint("sales_price >= 0", name="ck_product_variant_sales_price"),
        sa.CheckConstraint("purchase_price >= 0", name="ck_product_variant_purchase_price"),
    )
    op.create_index("ix_product_variants_company_id", "product_variants", ["company_id"])
    op.create_index("ix_product_variants_product_id", "product_variants", ["product_id"])

    op.create_table(
        "product_barcodes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("variant_id", sa.Integer(), sa.ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=True),
        sa.Column("barcode", sa.String(120), nullable=False),
        sa.Column("barcode_type", sa.String(30), nullable=False, server_default="EAN"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "barcode", name="uq_product_barcode_company_code"),
    )
    op.create_index("ix_product_barcodes_company_id", "product_barcodes", ["company_id"])
    op.create_index("ix_product_barcodes_product_id", "product_barcodes", ["product_id"])
    op.create_index("ix_product_barcodes_variant_id", "product_barcodes", ["variant_id"])


def downgrade():
    op.drop_table("product_barcodes")
    op.drop_table("product_variants")
    op.drop_index("ix_inventory_items_purchase_uom_id", table_name="inventory_items")
    op.drop_index("ix_inventory_items_sales_uom_id", table_name="inventory_items")
    op.drop_constraint("fk_inventory_items_purchase_uom", "inventory_items", type_="foreignkey")
    op.drop_constraint("fk_inventory_items_sales_uom", "inventory_items", type_="foreignkey")
    op.drop_column("inventory_items", "purchase_uom_id")
    op.drop_column("inventory_items", "sales_uom_id")
