"""Harden inventory company and variant integrity at database level.

Revision ID: 20260915_inventory_integrity_hardening
Revises: 20260915_enterprise_integrity_hardening
"""
from alembic import op
import sqlalchemy as sa

revision = "20260915_inventory_integrity_hardening"
down_revision = "20260915_enterprise_integrity_hardening"
branch_labels = None
depends_on = None


def _assert_clean(conn, sql: str, message: str) -> None:
    if conn.execute(sa.text(sql)).scalar():
        raise RuntimeError(message)


def upgrade():
    conn = op.get_bind()

    _assert_clean(
        conn,
        "SELECT EXISTS (SELECT 1 FROM inventory_warehouses w JOIN branches b ON b.id = w.branch_id WHERE w.branch_id IS NOT NULL AND (w.company_id <> b.company_id OR w.tenant_id <> b.tenant_id))",
        "Cannot harden inventory_warehouses: cross-company/tenant branch references exist.",
    )
    _assert_clean(
        conn,
        "SELECT EXISTS (SELECT 1 FROM inventory_locations l JOIN inventory_warehouses w ON w.id = l.warehouse_id WHERE l.company_id <> w.company_id)",
        "Cannot harden inventory_locations: warehouse belongs to another company.",
    )
    _assert_clean(
        conn,
        "SELECT EXISTS (SELECT 1 FROM inventory_locations child JOIN inventory_locations parent ON parent.id = child.parent_id WHERE child.company_id <> parent.company_id)",
        "Cannot harden inventory_locations: cross-company parent references exist.",
    )
    _assert_clean(
        conn,
        "SELECT EXISTS (SELECT 1 FROM inventory_stocks s JOIN inventory_items i ON i.id = s.item_id JOIN inventory_warehouses w ON w.id = s.warehouse_id WHERE s.company_id <> i.company_id OR s.company_id <> w.company_id)",
        "Cannot harden inventory_stocks: cross-company item/warehouse references exist.",
    )
    _assert_clean(
        conn,
        "SELECT EXISTS (SELECT 1 FROM inventory_stocks s JOIN product_variants v ON v.id = s.variant_id WHERE s.variant_id IS NOT NULL AND (s.company_id <> v.company_id OR s.item_id <> v.product_id))",
        "Cannot harden inventory_stocks: variant does not belong to the same company/product.",
    )
    _assert_clean(
        conn,
        "SELECT EXISTS (SELECT 1 FROM inventory_stock_moves m LEFT JOIN inventory_items i ON i.id = m.item_id LEFT JOIN product_variants v ON v.id = m.variant_id LEFT JOIN inventory_locations sl ON sl.id = m.source_location_id LEFT JOIN inventory_locations dl ON dl.id = m.destination_location_id WHERE i.id IS NULL OR m.company_id <> i.company_id OR (m.variant_id IS NOT NULL AND (v.id IS NULL OR m.company_id <> v.company_id OR m.item_id <> v.product_id)) OR (m.source_location_id IS NOT NULL AND (sl.id IS NULL OR m.company_id <> sl.company_id)) OR (m.destination_location_id IS NOT NULL AND (dl.id IS NULL OR m.company_id <> dl.company_id)))",
        "Cannot harden inventory_stock_moves: cross-company item/variant/location references exist.",
    )

    # Composite targets required by PostgreSQL for company-scoped foreign keys.
    op.create_unique_constraint("uq_inventory_warehouses_company_id", "inventory_warehouses", ["company_id", "id"])
    op.create_unique_constraint("uq_inventory_locations_company_id", "inventory_locations", ["company_id", "id"])
    op.create_unique_constraint("uq_inventory_items_company_id", "inventory_items", ["company_id", "id"])
    op.create_unique_constraint("uq_product_variants_company_product_id", "product_variants", ["company_id", "product_id", "id"])

    op.create_foreign_key(
        "fk_inventory_warehouse_branch_same_company",
        "inventory_warehouses",
        "branches",
        ["company_id", "branch_id"],
        ["company_id", "id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_inventory_location_warehouse_same_company",
        "inventory_locations",
        "inventory_warehouses",
        ["company_id", "warehouse_id"],
        ["company_id", "id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_inventory_location_parent_same_company",
        "inventory_locations",
        "inventory_locations",
        ["company_id", "parent_id"],
        ["company_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_inventory_stock_item_same_company",
        "inventory_stocks",
        "inventory_items",
        ["company_id", "item_id"],
        ["company_id", "id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_inventory_stock_warehouse_same_company",
        "inventory_stocks",
        "inventory_warehouses",
        ["company_id", "warehouse_id"],
        ["company_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_inventory_stock_variant_same_company_product",
        "inventory_stocks",
        "product_variants",
        ["company_id", "item_id", "variant_id"],
        ["company_id", "product_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_stock_move_item_same_company",
        "inventory_stock_moves",
        "inventory_items",
        ["company_id", "item_id"],
        ["company_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_stock_move_variant_same_company_product",
        "inventory_stock_moves",
        "product_variants",
        ["company_id", "item_id", "variant_id"],
        ["company_id", "product_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_stock_move_source_location_same_company",
        "inventory_stock_moves",
        "inventory_locations",
        ["company_id", "source_location_id"],
        ["company_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_stock_move_destination_location_same_company",
        "inventory_stock_moves",
        "inventory_locations",
        ["company_id", "destination_location_id"],
        ["company_id", "id"],
        ondelete="RESTRICT",
    )


def downgrade():
    op.drop_constraint("fk_stock_move_destination_location_same_company", "inventory_stock_moves", type_="foreignkey")
    op.drop_constraint("fk_stock_move_source_location_same_company", "inventory_stock_moves", type_="foreignkey")
    op.drop_constraint("fk_stock_move_variant_same_company_product", "inventory_stock_moves", type_="foreignkey")
    op.drop_constraint("fk_stock_move_item_same_company", "inventory_stock_moves", type_="foreignkey")
    op.drop_constraint("fk_inventory_stock_variant_same_company_product", "inventory_stocks", type_="foreignkey")
    op.drop_constraint("fk_inventory_stock_warehouse_same_company", "inventory_stocks", type_="foreignkey")
    op.drop_constraint("fk_inventory_stock_item_same_company", "inventory_stocks", type_="foreignkey")
    op.drop_constraint("fk_inventory_location_parent_same_company", "inventory_locations", type_="foreignkey")
    op.drop_constraint("fk_inventory_location_warehouse_same_company", "inventory_locations", type_="foreignkey")
    op.drop_constraint("fk_inventory_warehouse_branch_same_company", "inventory_warehouses", type_="foreignkey")
    op.drop_constraint("uq_product_variants_company_product_id", "product_variants", type_="unique")
    op.drop_constraint("uq_inventory_items_company_id", "inventory_items", type_="unique")
    op.drop_constraint("uq_inventory_locations_company_id", "inventory_locations", type_="unique")
    op.drop_constraint("uq_inventory_warehouses_company_id", "inventory_warehouses", type_="unique")
