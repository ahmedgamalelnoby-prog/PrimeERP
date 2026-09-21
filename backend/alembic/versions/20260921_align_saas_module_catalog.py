"""align SaaS module catalog with the canonical seeded ERP modules.

Revision ID: 20260921_align_saas_module_catalog
Revises: 20260921_integration_event_state_machine
"""

from alembic import op
import sqlalchemy as sa

revision = "20260921_align_saas_module_catalog"
down_revision = "20260921_integration_event_state_machine"
branch_labels = None
depends_on = None

MODULES = (
    ("purchasing", "المشتريات", "Purchasing", 35),
    ("crm", "إدارة العملاء", "CRM", 45),
    ("restaurant", "إدارة المطاعم", "Restaurant", 60),
    ("pos", "نقاط البيع", "Point of Sale", 70),
    ("hr", "الموارد البشرية", "Human Resources", 80),
    ("manufacturing", "التصنيع", "Manufacturing", 100),
    ("reports", "التقارير", "Reports", 120),
)


def upgrade():
    bind = op.get_bind()
    for code, name_ar, name_en, display_order in MODULES:
        bind.execute(
            sa.text(
                """
                INSERT INTO system_modules
                    (code, name_ar, name_en, is_core, is_active, display_order, created_at)
                VALUES
                    (:code, :name_ar, :name_en, false, true, :display_order, now())
                ON CONFLICT (code) DO UPDATE SET
                    name_ar = EXCLUDED.name_ar,
                    name_en = EXCLUDED.name_en,
                    is_active = true,
                    display_order = EXCLUDED.display_order
                """
            ),
            {"code": code, "name_ar": name_ar, "name_en": name_en, "display_order": display_order},
        )

    # Keep existing active plans compatible with the canonical module catalog.
    bind.execute(
        sa.text(
            """
            INSERT INTO plan_modules (plan_id, module_id, is_enabled)
            SELECT p.id, m.id, true
            FROM subscription_plans p
            JOIN system_modules m ON m.code IN (
                'purchasing','crm','restaurant','pos','hr','manufacturing','reports'
            )
            WHERE p.is_active = true
              AND NOT EXISTS (
                  SELECT 1 FROM plan_modules pm
                  WHERE pm.plan_id = p.id AND pm.module_id = m.id
              )
            """
        )
    )


def downgrade():
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            DELETE FROM plan_modules
            WHERE module_id IN (
                SELECT id FROM system_modules
                WHERE code IN ('purchasing','crm','restaurant','pos','hr','manufacturing','reports')
            )
            """
        )
    )
    bind.execute(
        sa.text(
            """
            DELETE FROM system_modules
            WHERE code IN ('purchasing','crm','restaurant','pos','hr','manufacturing','reports')
            """
        )
    )
