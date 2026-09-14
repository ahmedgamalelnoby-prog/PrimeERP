"""add variant dimension to inventory stock, movements, reservations and FIFO

Revision ID: 20260914_variant_inventory_dimension
Revises: 20260914_namespace_integration_product_mapping_external_ids
"""
from alembic import op
import sqlalchemy as sa

revision = "20260914_variant_inventory_dimension"
down_revision = "20260914_namespace_integration_product_mapping_external_ids"
branch_labels = None
depends_on = None


def _add_variant(table: str):
    op.add_column(table, sa.Column("variant_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        f"fk_{table}_variant_id",
        table,
        "product_variants",
        ["variant_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(f"ix_{table}_variant_id", table, ["variant_id"])


def upgrade():
    _add_variant("inventory_stocks")
    _add_variant("inventory_location_stocks")
    _add_variant("inventory_stock_moves")
    _add_variant("inventory_cost_layers")
    _add_variant("inventory_reservations")
    _add_variant("inventory_adjustments")

    op.drop_constraint("uq_inventory_stock_location", "inventory_stocks", type_="unique")
    op.create_index(
        "uq_inventory_stock_product",
        "inventory_stocks",
        ["company_id", "item_id", "warehouse_id"],
        unique=True,
        postgresql_where=sa.text("variant_id IS NULL"),
    )
    op.create_index(
        "uq_inventory_stock_variant",
        "inventory_stocks",
        ["company_id", "item_id", "variant_id", "warehouse_id"],
        unique=True,
        postgresql_where=sa.text("variant_id IS NOT NULL"),
    )

    op.drop_constraint("uq_inventory_location_stock", "inventory_location_stocks", type_="unique")
    op.create_index(
        "uq_inventory_location_stock_product",
        "inventory_location_stocks",
        ["company_id", "location_id", "item_id"],
        unique=True,
        postgresql_where=sa.text("variant_id IS NULL"),
    )
    op.create_index(
        "uq_inventory_location_stock_variant",
        "inventory_location_stocks",
        ["company_id", "location_id", "item_id", "variant_id"],
        unique=True,
        postgresql_where=sa.text("variant_id IS NOT NULL"),
    )


def downgrade():
    op.drop_index("uq_inventory_location_stock_variant", table_name="inventory_location_stocks")
    op.drop_index("uq_inventory_location_stock_product", table_name="inventory_location_stocks")
    op.create_unique_constraint("uq_inventory_location_stock", "inventory_location_stocks", ["company_id", "location_id", "item_id"])
    op.drop_index("uq_inventory_stock_variant", table_name="inventory_stocks")
    op.drop_index("uq_inventory_stock_product", table_name="inventory_stocks")
    op.create_unique_constraint("uq_inventory_stock_location", "inventory_stocks", ["company_id", "item_id", "warehouse_id"])

    for table in ["inventory_adjustments", "inventory_reservations", "inventory_cost_layers", "inventory_stock_moves", "inventory_location_stocks", "inventory_stocks"]:
        op.drop_index(f"ix_{table}_variant_id", table_name=table)
        op.drop_constraint(f"fk_{table}_variant_id", table, type_="foreignkey")
        op.drop_column(table, "variant_id")
