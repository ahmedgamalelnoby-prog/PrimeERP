"""Link recipes to the external commerce SKU used to sell the product."""
from alembic import op
import sqlalchemy as sa

revision = "20260919_recipe_external_sku"
down_revision = "20260919_generic_shipping_mapping"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("recipes", sa.Column("external_sku", sa.String(160), nullable=True))
    op.create_index("ix_recipes_company_external_sku", "recipes", ["company_id", "external_sku"])
    op.create_unique_constraint("uq_recipe_company_external_sku", "recipes", ["company_id", "external_sku"])

    # Existing commercial-product recipes inherit the external SKU already
    # captured by an integration product mapping. This is intentionally
    # company-scoped and does not change the ERP's internal recipe code.
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE recipes r
        SET external_sku = x.external_sku
        FROM (
            SELECT DISTINCT ON (ipm.company_id, ipm.catalog_product_id)
                   ipm.company_id, ipm.catalog_product_id, ipm.external_sku
            FROM integration_product_mappings ipm
            WHERE ipm.catalog_product_id IS NOT NULL
              AND ipm.external_sku IS NOT NULL
              AND trim(ipm.external_sku) <> ''
            ORDER BY ipm.company_id, ipm.catalog_product_id, ipm.updated_at DESC, ipm.id DESC
        ) x
        WHERE r.company_id = x.company_id
          AND r.catalog_product_id = x.catalog_product_id
          AND r.external_sku IS NULL
    """))

def downgrade() -> None:
    op.drop_constraint("uq_recipe_company_external_sku", "recipes", type_="unique")
    op.drop_index("ix_recipes_company_external_sku", table_name="recipes")
    op.drop_column("recipes", "external_sku")
