"""Seed SaaS entitlement rows for application service modules."""

from alembic import op
import sqlalchemy as sa


revision = "20260918_application_module_entitlements"
down_revision = "20260917_application_services_core"
branch_labels = None
depends_on = None

MODULES = (
    ("helpdesk", "Helpdesk", "نظام خدمة العملاء والدعم", "نظام خدمة العملاء والدعم", "Helpdesk application services", 500),
    ("project", "Project", "إدارة المشاريع والمهام", "إدارة المشاريع والمهام", "Project management and task services", 501),
    ("documents", "Documents", "إدارة المستندات والملفات", "إدارة المستندات والملفات", "Document management and file services", 502),
)


def upgrade() -> None:
    statement = sa.text(
        """
        INSERT INTO system_modules
            (code, name_ar, name_en, description_ar, description_en, is_core, is_active, display_order)
        VALUES
            (:code, :name_ar, :name_en, :description_ar, :description_en, false, true, :display_order)
        ON CONFLICT (code) DO UPDATE SET
            name_ar = EXCLUDED.name_ar,
            name_en = EXCLUDED.name_en,
            description_ar = EXCLUDED.description_ar,
            description_en = EXCLUDED.description_en,
            is_active = true,
            display_order = EXCLUDED.display_order
        """
    )
    for code, name_en, name_ar, description_ar, description_en, display_order in MODULES:
        op.execute(
            statement.bindparams(
                code=code,
                name_ar=name_ar,
                name_en=name_en,
                description_ar=description_ar,
                description_en=description_en,
                display_order=display_order,
            )
        )

    op.execute(
        sa.text(
            """
            INSERT INTO plan_modules (plan_id, module_id, is_enabled)
            SELECT p.id, m.id, true
            FROM subscription_plans p
            CROSS JOIN system_modules m
            WHERE p.code = 'professional'
              AND m.code IN ('helpdesk', 'project', 'documents')
            ON CONFLICT (plan_id, module_id) DO UPDATE SET is_enabled = true
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM plan_modules
            WHERE module_id IN (
                SELECT id FROM system_modules
                WHERE code IN ('helpdesk', 'project', 'documents')
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            DELETE FROM system_modules
            WHERE code IN ('helpdesk', 'project', 'documents')
            """
        )
    )
