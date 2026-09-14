"""snapshot recipe line UOM conversion

Revision ID: 20260914_recipe_uom_snapshot
Revises: 20260914_catalog_integrity
"""
from alembic import op
import sqlalchemy as sa

revision = "20260914_recipe_uom_snapshot"
down_revision = "20260914_catalog_integrity"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "recipe_lines",
        sa.Column("conversion_factor_to_product_uom", sa.Numeric(18, 8), nullable=True, server_default="1"),
    )
    # Existing rows historically assumed quantities were already in the
    # ingredient product UOM. Preserve that interpretation. New rows are
    # populated by the catalog service from the current UOM master data.
    op.execute(
        "UPDATE recipe_lines SET conversion_factor_to_product_uom = 1 "
        "WHERE conversion_factor_to_product_uom IS NULL"
    )
    op.alter_column(
        "recipe_lines",
        "conversion_factor_to_product_uom",
        nullable=False,
        server_default="1",
    )
    op.create_check_constraint(
        "ck_recipe_line_conversion_positive",
        "recipe_lines",
        "conversion_factor_to_product_uom > 0",
    )
    op.create_index(
        "ix_recipe_line_ingredient_uom",
        "recipe_lines",
        ["ingredient_product_id", "uom_id"],
    )


def downgrade():
    op.drop_index("ix_recipe_line_ingredient_uom", table_name="recipe_lines")
    op.drop_constraint("ck_recipe_line_conversion_positive", "recipe_lines", type_="check")
    op.drop_column("recipe_lines", "conversion_factor_to_product_uom")
