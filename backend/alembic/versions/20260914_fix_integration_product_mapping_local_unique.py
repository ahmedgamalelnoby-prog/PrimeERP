"""fix nullable variant uniqueness for integration product mappings

Revision ID: 20260914_fix_integration_product_mapping_local_unique
Revises: 20260914_integration_product_mappings
"""
from alembic import op
import sqlalchemy as sa

revision = "20260914_fix_integration_product_mapping_local_unique"
down_revision = "20260914_integration_product_mappings"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint(
        "uq_integration_product_mapping_local",
        "integration_product_mappings",
        type_="unique",
    )
    op.create_index(
        "uq_integration_product_mapping_local_variant",
        "integration_product_mappings",
        ["connection_id", "product_id", "variant_id"],
        unique=True,
        postgresql_where=sa.text("variant_id IS NOT NULL"),
    )
    op.create_index(
        "uq_integration_product_mapping_local_product",
        "integration_product_mappings",
        ["connection_id", "product_id"],
        unique=True,
        postgresql_where=sa.text("variant_id IS NULL"),
    )


def downgrade():
    op.drop_index(
        "uq_integration_product_mapping_local_product",
        table_name="integration_product_mappings",
    )
    op.drop_index(
        "uq_integration_product_mapping_local_variant",
        table_name="integration_product_mappings",
    )
    op.create_unique_constraint(
        "uq_integration_product_mapping_local",
        "integration_product_mappings",
        ["connection_id", "product_id", "variant_id"],
    )
