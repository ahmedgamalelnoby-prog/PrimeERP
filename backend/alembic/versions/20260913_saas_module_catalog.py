"""seed the ERP module catalog and preserve access for existing plans

Revision ID: 20260913_saas_module_catalog
Revises: 20260913_plan_entitlements
"""

from alembic import op
import sqlalchemy as sa


revision = "20260913_saas_module_catalog"
down_revision = "20260913_plan_entitlements"
branch_labels = None
depends_on = None

MODULES = (
    ("accounting", "المحاسبة", "Accounting", False, 10),
    ("inventory", "المخزون", "Inventory", False, 20),
    ("sales", "المبيعات والمشتريات", "Sales & Purchasing", False, 30),
    ("treasury", "الخزينة", "Treasury", False, 40),
    ("shipping", "الشحن", "Shipping", False, 50),
    ("integrations", "التكاملات", "Integrations", False, 60),
    ("enterprise", "إدارة المؤسسة", "Enterprise", False, 70),
    ("einvoice", "الفاتورة الإلكترونية", "Egyptian E-Invoicing", False, 80),
)


def upgrade():
    conn = op.get_bind()
    for code, name_ar, name_en, is_core, display_order in MODULES:
        conn.execute(
            sa.text(
                """
                INSERT INTO system_modules
                    (code, name_ar, name_en, is_core, is_active, display_order, created_at)
                VALUES
                    (:code, :name_ar, :name_en, :is_core, true, :display_order, now())
                ON CONFLICT (code) DO UPDATE SET
                    name_ar = EXCLUDED.name_ar,
                    name_en = EXCLUDED.name_en,
                    is_active = true,
                    display_order = EXCLUDED.display_order
                """
            ),
            {
                "code": code,
                "name_ar": name_ar,
                "name_en": name_en,
                "is_core": is_core,
                "display_order": display_order,
            },
        )

    # Existing subscription plans must keep their current ERP access. Platform
    # administrators can narrow access afterwards through PlanModule settings.
    conn.execute(
        sa.text(
            """
            INSERT INTO plan_modules (plan_id, module_id, is_enabled)
            SELECT p.id, m.id, true
            FROM subscription_plans p
            CROSS JOIN system_modules m
            WHERE p.is_active = true
              AND NOT EXISTS (
                  SELECT 1 FROM plan_modules pm
                  WHERE pm.plan_id = p.id AND pm.module_id = m.id
              )
            """
        )
    )


def downgrade():
    conn = op.get_bind()
    codes = [code for code, *_ in MODULES]
    conn.execute(
        sa.text("DELETE FROM plan_modules WHERE module_id IN (SELECT id FROM system_modules WHERE code = ANY(:codes))"),
        {"codes": codes},
    )
    conn.execute(
        sa.text("DELETE FROM system_modules WHERE code = ANY(:codes)"),
        {"codes": codes},
    )
