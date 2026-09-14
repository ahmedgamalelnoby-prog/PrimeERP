"""Add product catalog, pricing, recipes and menus.

Revision ID: 20260914_product_catalog
Revises: 20260914_audit_login_indexes
"""
from alembic import op
import sqlalchemy as sa

revision = "20260914_product_catalog"
down_revision = "20260914_audit_login_indexes"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "product_categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("product_categories.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name_ar", sa.String(160), nullable=False),
        sa.Column("name_en", sa.String(160)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "code", name="uq_product_category_company_code"),
    )
    op.create_index("ix_product_categories_company_id", "product_categories", ["company_id"])
    op.create_index("ix_product_categories_parent_id", "product_categories", ["parent_id"])

    op.create_table(
        "product_price_lists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EGP"),
        sa.Column("channel", sa.String(30), nullable=False, server_default="default"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "code", name="uq_price_list_company_code"),
    )
    op.create_index("ix_product_price_lists_company_id", "product_price_lists", ["company_id"])
    op.create_index("ux_price_list_single_default", "product_price_lists", ["company_id"], unique=True, postgresql_where=sa.text("is_default = true"))

    op.create_table(
        "product_prices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("price_list_id", sa.Integer(), sa.ForeignKey("product_price_lists.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sale_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("min_quantity", sa.Numeric(18, 4), nullable=False, server_default="1"),
        sa.Column("valid_from", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("valid_to", sa.DateTime()),
        sa.Column("source", sa.String(30), nullable=False, server_default="manual"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("sale_price >= 0", name="ck_product_price_nonnegative"),
        sa.CheckConstraint("min_quantity > 0", name="ck_product_price_min_qty"),
    )
    op.create_index("ix_product_prices_company_id", "product_prices", ["company_id"])
    op.create_index("ix_product_prices_price_list_id", "product_prices", ["price_list_id"])
    op.create_index("ix_product_prices_product_id", "product_prices", ["product_id"])

    op.create_table(
        "product_cost_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cost", sa.Numeric(18, 4), nullable=False),
        sa.Column("cost_type", sa.String(30), nullable=False, server_default="standard"),
        sa.Column("source", sa.String(50), nullable=False, server_default="manual"),
        sa.Column("effective_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("note", sa.Text()),
        sa.CheckConstraint("cost >= 0", name="ck_product_cost_nonnegative"),
    )
    op.create_index("ix_product_cost_history_company_id", "product_cost_history", ["company_id"])
    op.create_index("ix_product_cost_history_product_id", "product_cost_history", ["product_id"])
    op.create_index("ix_product_cost_history_effective_at", "product_cost_history", ["effective_at"])

    op.create_table(
        "recipes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("name_ar", sa.String(200), nullable=False),
        sa.Column("name_en", sa.String(200)),
        sa.Column("yield_quantity", sa.Numeric(18, 4), nullable=False, server_default="1"),
        sa.Column("waste_percentage", sa.Numeric(7, 4), nullable=False, server_default="0"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "code", "version", name="uq_recipe_company_code_version"),
        sa.UniqueConstraint("company_id", "product_id", "version", name="uq_recipe_company_product_version"),
        sa.CheckConstraint("yield_quantity > 0", name="ck_recipe_yield_positive"),
        sa.CheckConstraint("waste_percentage >= 0 AND waste_percentage < 100", name="ck_recipe_waste_range"),
    )
    op.create_index("ix_recipes_company_id", "recipes", ["company_id"])
    op.create_index("ix_recipes_product_id", "recipes", ["product_id"])

    op.create_table(
        "recipe_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("recipe_id", sa.Integer(), sa.ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("line_no", sa.Integer(), nullable=False),
        sa.Column("ingredient_product_id", sa.Integer(), sa.ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("waste_percentage", sa.Numeric(7, 4), nullable=False, server_default="0"),
        sa.Column("uom_id", sa.Integer(), sa.ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("notes", sa.String(500)),
        sa.UniqueConstraint("recipe_id", "line_no", name="uq_recipe_line_no"),
        sa.CheckConstraint("line_no > 0", name="ck_recipe_line_no_positive"),
        sa.CheckConstraint("quantity > 0", name="ck_recipe_line_quantity_positive"),
        sa.CheckConstraint("waste_percentage >= 0 AND waste_percentage < 100", name="ck_recipe_line_waste_range"),
    )
    op.create_index("ix_recipe_lines_recipe_id", "recipe_lines", ["recipe_id"])
    op.create_index("ix_recipe_lines_ingredient_product_id", "recipe_lines", ["ingredient_product_id"])

    op.create_table(
        "menus",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.Integer(), sa.ForeignKey("branches.id", ondelete="CASCADE"), nullable=True),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("name_ar", sa.String(200), nullable=False),
        sa.Column("name_en", sa.String(200)),
        sa.Column("description", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("published_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "code", name="uq_menu_company_code"),
    )
    op.create_index("ix_menus_company_id", "menus", ["company_id"])
    op.create_index("ix_menus_branch_id", "menus", ["branch_id"])

    op.create_table(
        "menu_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("menu_id", sa.Integer(), sa.ForeignKey("menus.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("price_list_id", sa.Integer(), sa.ForeignKey("product_price_lists.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("sale_price_override", sa.Numeric(18, 4)),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("menu_id", "product_id", name="uq_menu_product"),
        sa.CheckConstraint("sale_price_override IS NULL OR sale_price_override >= 0", name="ck_menu_override_price"),
    )
    op.create_index("ix_menu_items_menu_id", "menu_items", ["menu_id"])
    op.create_index("ix_menu_items_product_id", "menu_items", ["product_id"])
    op.create_index("ix_menu_items_price_list_id", "menu_items", ["price_list_id"])


def downgrade():
    op.drop_table("menu_items")
    op.drop_table("menus")
    op.drop_table("recipe_lines")
    op.drop_table("recipes")
    op.drop_table("product_cost_history")
    op.drop_table("product_prices")
    op.drop_index("ux_price_list_single_default", table_name="product_price_lists")
    op.drop_table("product_price_lists")
    op.drop_table("product_categories")
