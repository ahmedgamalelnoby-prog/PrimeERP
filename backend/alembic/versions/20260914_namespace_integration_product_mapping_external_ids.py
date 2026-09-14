"""namespace integration product mapping external ids

Revision ID: 20260914_namespace_integration_product_mapping_external_ids
Revises: 20260914_sales_line_variant
"""
from alembic import op
import sqlalchemy as sa

revision = "20260914_namespace_integration_product_mapping_external_ids"
down_revision = "20260914_sales_line_variant"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "integration_product_mappings",
        sa.Column("entity_type", sa.String(20), nullable=False, server_default="product"),
    )
    op.execute(
        "UPDATE integration_product_mappings SET entity_type = 'variant' WHERE variant_id IS NOT NULL"
    )
    op.create_check_constraint(
        "ck_integration_product_mapping_entity_type",
        "integration_product_mappings",
        "entity_type IN ('product','variant')",
    )
    op.drop_constraint(
        "uq_integration_product_mapping_external",
        "integration_product_mappings",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_integration_product_mapping_external",
        "integration_product_mappings",
        ["connection_id", "entity_type", "external_id"],
    )


def downgrade():
    op.drop_constraint(
        "uq_integration_product_mapping_external",
        "integration_product_mappings",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_integration_product_mapping_external",
        "integration_product_mappings",
        ["connection_id", "external_id"],
    )
    op.drop_constraint(
        "ck_integration_product_mapping_entity_type",
        "integration_product_mappings",
        type_="check",
    )
    op.drop_column("integration_product_mappings", "entity_type")
