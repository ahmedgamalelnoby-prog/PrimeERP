"""Add variant identity to recipes.

Revision ID: 20260919_recipe_variant_identity
Revises: 20260919_recipe_sku_mapping
"""
from alembic import op
import sqlalchemy as sa

revision = "20260919_recipe_variant_identity"
down_revision = "20260919_recipe_sku_mapping"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("recipes", sa.Column("variant_id", sa.Integer(), sa.ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=True))
    op.create_index("ix_recipes_variant_id", "recipes", ["variant_id"])
    op.drop_constraint("uq_recipe_company_product_version", "recipes", type_="unique")
    op.create_index(
        "uq_recipe_company_product_version_parent",
        "recipes",
        ["company_id", "product_id", "version"],
        unique=True,
        postgresql_where=sa.text("variant_id IS NULL"),
    )
    op.create_index(
        "uq_recipe_company_product_variant_version",
        "recipes",
        ["company_id", "product_id", "variant_id", "version"],
        unique=True,
        postgresql_where=sa.text("variant_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_recipe_company_product_variant_version", table_name="recipes")
    op.drop_index("uq_recipe_company_product_version_parent", table_name="recipes")
    op.create_unique_constraint("uq_recipe_company_product_version", "recipes", ["company_id", "product_id", "version"])
    op.drop_index("ix_recipes_variant_id", table_name="recipes")
    op.drop_column("recipes", "variant_id")
