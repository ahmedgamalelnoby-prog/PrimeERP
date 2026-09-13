"""link inventory items to the canonical unit-of-measure master

Revision ID: 20260913_inventory_uom_integration
Revises: 20260913_saas_module_catalog
"""

from alembic import op
import sqlalchemy as sa


revision = "20260913_inventory_uom_integration"
down_revision = "20260913_saas_module_catalog"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "inventory_items",
        sa.Column("uom_id", sa.Integer(), nullable=True),
    )
    op.create_index("ix_inventory_items_uom_id", "inventory_items", ["uom_id"], unique=False)
    op.create_foreign_key(
        "fk_inventory_items_uom_id",
        "inventory_items",
        "units_of_measure",
        ["uom_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # Seed canonical UOMs for every existing company. Codes are intentionally
    # stable so integrations can use them without depending on numeric IDs.
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO units_of_measure
                (company_id, code, name, category, factor_to_base, is_base, is_active)
            SELECT c.id, v.code, v.name, v.category, v.factor_to_base, v.is_base, true
            FROM companies c
            CROSS JOIN (
                VALUES
                    ('unit', 'Unit', 'quantity', 1::numeric, true),
                    ('kg', 'Kilogram', 'weight', 1::numeric, true),
                    ('g', 'Gram', 'weight', 0.001::numeric, false),
                    ('ton', 'Ton', 'weight', 1000::numeric, false),
                    ('liter', 'Liter', 'volume', 1::numeric, true),
                    ('ml', 'Milliliter', 'volume', 0.001::numeric, false)
            ) AS v(code, name, category, factor_to_base, is_base)
            ON CONFLICT (company_id, code) DO NOTHING
            """
        )
    )

    # Preserve existing legacy UOM codes by creating company-scoped master
    # records when a product uses a custom code, then backfill the FK.
    conn.execute(
        sa.text(
            """
            INSERT INTO units_of_measure
                (company_id, code, name, category, factor_to_base, is_base, is_active)
            SELECT DISTINCT i.company_id, i.uom, i.uom, 'custom', 1, true, true
            FROM inventory_items i
            WHERE i.uom IS NOT NULL
              AND trim(i.uom) <> ''
              AND NOT EXISTS (
                  SELECT 1
                  FROM units_of_measure u
                  WHERE u.company_id = i.company_id
                    AND u.code = i.uom
              )
            ON CONFLICT (company_id, code) DO NOTHING
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE inventory_items i
            SET uom_id = u.id
            FROM units_of_measure u
            WHERE u.company_id = i.company_id
              AND u.code = i.uom
              AND i.uom_id IS NULL
            """
        )
    )


def downgrade():
    op.drop_constraint("fk_inventory_items_uom_id", "inventory_items", type_="foreignkey")
    op.drop_index("ix_inventory_items_uom_id", table_name="inventory_items")
    op.drop_column("inventory_items", "uom_id")
