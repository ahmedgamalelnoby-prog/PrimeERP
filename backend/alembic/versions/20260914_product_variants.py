"""add product variants and barcodes

Revision ID: 20260914_product_variants
Revises: 20260914_recipe_uom_snapshot
"""
from alembic import op
import sqlalchemy as sa

revision = "20260914_product_variants"
down_revision = "20260914_recipe_uom_snapshot"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "product_variants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sku", sa.String(100), nullable=False),
        sa.Column("name_ar", sa.String(200), nullable=False),
        sa.Column("name_en", sa.String(200)),
        sa.Column("attributes", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("uom_id", sa.Integer(), sa.ForeignKey("units_of_measure.id", ondelete="RESTRICT")),
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
        sa.Column("variant_id", sa.Integer(), sa.ForeignKey("product_variants.id", ondelete="CASCADE")),
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
    op.create_index(
        "ux_product_primary_barcode",
        "product_barcodes",
        ["company_id", "product_id"],
        unique=True,
        postgresql_where=sa.text("is_primary = true AND is_active = true"),
    )


def downgrade():
    op.drop_index("ux_product_primary_barcode", table_name="product_barcodes")
    op.drop_index("ix_product_barcodes_variant_id", table_name="product_barcodes")
    op.drop_index("ix_product_barcodes_product_id", table_name="product_barcodes")
    op.drop_index("ix_product_barcodes_company_id", table_name="product_barcodes")
    op.drop_table("product_barcodes")
    op.drop_index("ix_product_variants_product_id", table_name="product_variants")
    op.drop_index("ix_product_variants_company_id", table_name="product_variants")
    op.drop_table("product_variants")
