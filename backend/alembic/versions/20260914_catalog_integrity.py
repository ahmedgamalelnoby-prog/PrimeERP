"""catalog integrity guards

Revision ID: 20260914_catalog_integrity
Revises: 20260914_product_catalog
"""
from alembic import op

revision = "20260914_catalog_integrity"
down_revision = "20260914_product_catalog"
branch_labels = None
depends_on = None


def upgrade():
    # Prevent negative/zero recipe and pricing values even when writes bypass the API.
    op.create_check_constraint(
        "ck_recipe_yield_positive_db",
        "recipes",
        "yield_quantity > 0",
    )
    op.create_check_constraint(
        "ck_product_price_positive_db",
        "product_prices",
        "sale_price >= 0 AND min_quantity > 0",
    )
    op.create_check_constraint(
        "ck_recipe_line_quantity_positive_db",
        "recipe_lines",
        "quantity > 0",
    )
    # A product can have only one active recipe version at a time.
    op.create_index(
        "ux_recipe_one_active_product",
        "recipes",
        ["company_id", "product_id"],
        unique=True,
        postgresql_where="is_active = true",
    )
    # Fast current-price/current-recipe lookups and history analysis.
    op.create_index(
        "ix_product_price_current_lookup",
        "product_prices",
        ["company_id", "product_id", "price_list_id", "min_quantity", "valid_from", "valid_to"],
    )


def downgrade():
    op.drop_index("ix_product_price_current_lookup", table_name="product_prices")
    op.drop_index("ux_recipe_one_active_product", table_name="recipes")
    op.drop_constraint("ck_recipe_line_quantity_positive_db", "recipe_lines", type_="check")
    op.drop_constraint("ck_product_price_positive_db", "product_prices", type_="check")
    op.drop_constraint("ck_recipe_yield_positive_db", "recipes", type_="check")
