"""Enforce inventory product category ownership by foreign key.

Revision ID: 20260914_product_category_fk
Revises: 20260914_catalog_integrity
"""
from alembic import op
import sqlalchemy as sa

revision = "20260914_product_category_fk"
down_revision = "20260914_catalog_integrity"
branch_labels = None
depends_on = None


def upgrade():
    # Legacy inventory rows may contain category IDs created before the catalog
    # module existed. Clear only orphaned references before enforcing the FK.
    op.execute(
        sa.text(
            """
            UPDATE inventory_items
            SET category_id = NULL
            WHERE category_id IS NOT NULL
              AND category_id NOT IN (SELECT id FROM product_categories)
            """
        )
    )
    op.create_foreign_key(
        "fk_inventory_items_category_id_product_categories",
        "inventory_items",
        "product_categories",
        ["category_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint(
        "fk_inventory_items_category_id_product_categories",
        "inventory_items",
        type_="foreignkey",
    )
