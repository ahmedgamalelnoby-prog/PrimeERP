"""Introduce explicit Product identity separate from stock Item identity."""
from alembic import op
import sqlalchemy as sa

revision = "20260919_product_item_semantics"
down_revision = "20260919_salla_subscription_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "catalog_products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name_ar", sa.String(200), nullable=False),
        sa.Column("name_en", sa.String(200)),
        sa.Column("product_kind", sa.String(30), nullable=False, server_default="manufactured"),
        sa.Column("is_sellable", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "code", name="uq_catalog_product_company_code"),
        sa.UniqueConstraint("company_id", "item_id", name="uq_catalog_product_company_item"),
        sa.CheckConstraint("product_kind IN ('manufactured','traded','assembled','bundle','service')", name="ck_catalog_product_kind"),
    )
    op.create_index("ix_catalog_products_company_id", "catalog_products", ["company_id"])
    op.create_index("ix_catalog_products_item_id", "catalog_products", ["item_id"])

    # Add all dependent columns before any backfill SQL references them.
    op.add_column("recipes", sa.Column("catalog_product_id", sa.Integer(), nullable=True))
    op.add_column("recipe_lines", sa.Column("ingredient_item_id", sa.Integer(), nullable=True))
    op.add_column("product_bundles", sa.Column("catalog_product_id", sa.Integer(), nullable=True))
    op.add_column("product_bundle_lines", sa.Column("component_item_id", sa.Integer(), nullable=True))
    op.add_column("product_prices", sa.Column("catalog_product_id", sa.Integer(), nullable=True))
    op.add_column("sales_lines", sa.Column("catalog_product_id", sa.Integer(), nullable=True))
    op.add_column("purchase_lines", sa.Column("catalog_product_id", sa.Integer(), nullable=True))
    op.add_column("integration_product_mappings", sa.Column("catalog_product_id", sa.Integer(), nullable=True))

    op.create_foreign_key("fk_recipe_lines_ingredient_item", "recipe_lines", "inventory_items", ["ingredient_item_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_recipes_catalog_product", "recipes", "catalog_products", ["catalog_product_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_product_bundle_lines_component_item", "product_bundle_lines", "inventory_items", ["component_item_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_product_bundles_catalog_product", "product_bundles", "catalog_products", ["catalog_product_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_product_prices_catalog_product", "product_prices", "catalog_products", ["catalog_product_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_sales_lines_catalog_product", "sales_lines", "catalog_products", ["catalog_product_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_purchase_lines_catalog_product", "purchase_lines", "catalog_products", ["catalog_product_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_integration_product_mappings_catalog_product", "integration_product_mappings", "catalog_products", ["catalog_product_id"], ["id"], ondelete="RESTRICT")

    for index_name, table, column in [
        ("ix_recipe_lines_ingredient_item_id", "recipe_lines", "ingredient_item_id"),
        ("ix_recipes_catalog_product_id", "recipes", "catalog_product_id"),
        ("ix_product_bundle_lines_component_item_id", "product_bundle_lines", "component_item_id"),
        ("ix_product_bundles_catalog_product_id", "product_bundles", "catalog_product_id"),
        ("ix_product_prices_catalog_product_id", "product_prices", "catalog_product_id"),
        ("ix_sales_lines_catalog_product_id", "sales_lines", "catalog_product_id"),
        ("ix_purchase_lines_catalog_product_id", "purchase_lines", "catalog_product_id"),
        ("ix_integration_product_mappings_catalog_product_id", "integration_product_mappings", "catalog_product_id"),
    ]:
        op.create_index(index_name, table, [column])

    conn = op.get_bind()
    conn.execute(sa.text("""
        INSERT INTO catalog_products (company_id, item_id, code, name_ar, name_en, product_kind, is_sellable, is_active)
        SELECT i.company_id, i.id, i.sku, i.name_ar, i.name_en,
               CASE WHEN i.item_type = 'service' THEN 'service' ELSE 'traded' END,
               true, i.is_active
        FROM inventory_items i
        WHERE NOT EXISTS (
            SELECT 1 FROM catalog_products p
            WHERE p.company_id = i.company_id AND p.item_id = i.id
        )
    """))
    conn.execute(sa.text("""
        UPDATE recipe_lines SET ingredient_item_id = ingredient_product_id
        WHERE ingredient_item_id IS NULL
    """))
    conn.execute(sa.text("""
        UPDATE product_bundle_lines SET component_item_id = component_product_id
        WHERE component_item_id IS NULL
    """))
    conn.execute(sa.text("""
        UPDATE recipes r SET catalog_product_id = p.id
        FROM catalog_products p
        WHERE p.company_id = r.company_id AND p.item_id = r.product_id
    """))
    conn.execute(sa.text("""
        UPDATE product_bundles b SET catalog_product_id = p.id
        FROM catalog_products p
        WHERE p.company_id = b.company_id AND p.item_id = b.product_id
    """))
    conn.execute(sa.text("""
        UPDATE product_prices pp SET catalog_product_id = p.id
        FROM catalog_products p
        WHERE p.company_id = pp.company_id AND p.item_id = pp.product_id
    """))
    conn.execute(sa.text("""
        UPDATE sales_lines sl SET catalog_product_id = p.id
        FROM catalog_products p, sales_documents sd
        WHERE sd.id = sl.document_id
          AND p.company_id = sd.company_id
          AND p.item_id = sl.item_id
    """))
    conn.execute(sa.text("""
        UPDATE purchase_lines pl SET catalog_product_id = p.id
        FROM catalog_products p, purchase_documents pd
        WHERE pd.id = pl.document_id
          AND p.company_id = pd.company_id
          AND p.item_id = pl.item_id
    """))
    conn.execute(sa.text("""
        UPDATE integration_product_mappings ipm SET catalog_product_id = p.id
        FROM catalog_products p
        WHERE p.company_id = ipm.company_id AND p.item_id = ipm.product_id
    """))


def downgrade() -> None:
    for index_name, table in [
        ("ix_integration_product_mappings_catalog_product_id", "integration_product_mappings"),
        ("ix_purchase_lines_catalog_product_id", "purchase_lines"),
        ("ix_sales_lines_catalog_product_id", "sales_lines"),
        ("ix_product_prices_catalog_product_id", "product_prices"),
        ("ix_product_bundles_catalog_product_id", "product_bundles"),
        ("ix_product_bundle_lines_component_item_id", "product_bundle_lines"),
        ("ix_recipes_catalog_product_id", "recipes"),
        ("ix_recipe_lines_ingredient_item_id", "recipe_lines"),
    ]:
        op.drop_index(index_name, table_name=table)
    for constraint, table in [
        ("fk_integration_product_mappings_catalog_product", "integration_product_mappings"),
        ("fk_purchase_lines_catalog_product", "purchase_lines"),
        ("fk_sales_lines_catalog_product", "sales_lines"),
        ("fk_product_prices_catalog_product", "product_prices"),
        ("fk_product_bundles_catalog_product", "product_bundles"),
        ("fk_product_bundle_lines_component_item", "product_bundle_lines"),
        ("fk_recipes_catalog_product", "recipes"),
        ("fk_recipe_lines_ingredient_item", "recipe_lines"),
    ]:
        op.drop_constraint(constraint, table, type_="foreignkey")
    for table, column in [
        ("integration_product_mappings", "catalog_product_id"),
        ("purchase_lines", "catalog_product_id"),
        ("sales_lines", "catalog_product_id"),
        ("product_prices", "catalog_product_id"),
        ("product_bundle_lines", "component_item_id"),
        ("product_bundles", "catalog_product_id"),
        ("recipe_lines", "ingredient_item_id"),
        ("recipes", "catalog_product_id"),
    ]:
        op.drop_column(table, column)
    op.drop_index("ix_catalog_products_item_id", table_name="catalog_products")
    op.drop_index("ix_catalog_products_company_id", table_name="catalog_products")
    op.drop_table("catalog_products")
