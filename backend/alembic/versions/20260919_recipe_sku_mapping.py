"""Add dedicated recipe SKU identity mappings.

Revision ID: 20260919_recipe_sku_mapping
Revises: 20260919_payment_allocations
"""
from alembic import op
import sqlalchemy as sa

revision = "20260919_recipe_sku_mapping"
down_revision = "20260919_payment_allocations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recipe_sku_mappings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recipe_id", sa.Integer(), sa.ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("variant_id", sa.Integer(), sa.ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("sku", sa.String(160), nullable=False),
        sa.Column("source", sa.String(40), nullable=False, server_default="salla"),
        sa.Column("external_id", sa.String(160), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "sku", name="uq_recipe_sku_mapping_company_sku"),
        sa.UniqueConstraint("company_id", "source", "external_id", name="uq_recipe_sku_mapping_source_external"),
    )
    op.create_index("ix_recipe_sku_mappings_company_id", "recipe_sku_mappings", ["company_id"])
    op.create_index("ix_recipe_sku_mappings_recipe_id", "recipe_sku_mappings", ["recipe_id"])
    op.create_index("ix_recipe_sku_mappings_product_id", "recipe_sku_mappings", ["product_id"])
    op.create_index("ix_recipe_sku_mappings_variant_id", "recipe_sku_mappings", ["variant_id"])
    op.create_index("ix_recipe_sku_mappings_sku", "recipe_sku_mappings", ["sku"])


def downgrade() -> None:
    op.drop_table("recipe_sku_mappings")
