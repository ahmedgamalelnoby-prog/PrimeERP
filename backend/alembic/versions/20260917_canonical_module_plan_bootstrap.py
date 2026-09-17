"""Establish one executable SaaS module/plan catalog.

This migration does not create demo tenants or credentials. It makes the
production catalog deterministic and keeps the legacy subscription tables as a
compatibility persistence boundary until subscriptions are fully migrated.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "20260917_canonical_module_plan_bootstrap"
down_revision = "20260916_release_graph_absolute_merge"
branch_labels = None
depends_on = None

MODULES = (
    ("dashboard", "Dashboard", "لوحة التحكم", True, 5),
    ("users", "Users & Access", "المستخدمون والصلاحيات", True, 10),
    ("companies", "Companies", "الشركات", True, 15),
    ("branches", "Branches", "الفروع", True, 20),
    ("accounting", "Accounting", "المحاسبة", True, 100),
    ("taxes", "Taxes", "الضرائب", True, 140),
    ("sales", "Sales", "المبيعات", True, 205),
    ("purchasing", "Purchase", "المشتريات", True, 300),
    ("inventory", "Inventory", "المخزون", True, 305),
    ("shipping", "Shipping & Delivery", "الشحن والتوصيل", False, 315),
    ("uom", "Units of Measure", "وحدات القياس", True, 345),
    ("integrations", "Integrations", "التكاملات", False, 610),
    ("enterprise", "Enterprise Operations", "عمليات المؤسسات", False, 620),
    ("commissions", "Sales Commissions", "عمولات المبيعات", False, 220),
    ("treasury", "Treasury", "الخزينة", True, 360),
    ("einvoice", "Egyptian e-Invoice", "الفاتورة الإلكترونية المصرية", False, 145),
    ("audit", "Audit", "المراجعة والتدقيق", True, 750),
    ("roles", "Roles & Permissions", "الأدوار والصلاحيات", True, 755),
    ("catalog", "Product Catalog", "كتالوج المنتجات", False, 350),
    ("reports", "Reporting & BI", "التقارير والتحليلات", True, 740),
    ("legal", "Legal", "الشؤون القانونية", False, 760),
    ("jurisdiction", "Jurisdiction", "الاختصاص والبيانات القانونية", False, 765),
    ("transactions", "Transactions", "المعاملات", True, 370),
    ("commerce", "Commerce", "التجارة", False, 375),
)

PLAN_ENTITLEMENTS = {
    "trial": {
        "dashboard", "users", "companies", "branches", "accounting", "sales", "inventory", "reports",
    },
    "starter": {
        "dashboard", "users", "companies", "branches", "accounting", "sales", "inventory", "purchasing", "reports",
    },
    "professional": {code for code, *_ in MODULES},
}

PLANS = (
    {
        "code": "trial", "name": "Trial", "name_ar": "تجريبي", "monthly": 0, "yearly": 0,
        "trial_days": 14, "max_users": 5, "max_companies": 1, "max_branches": 2,
        "max_products": 1000, "max_integrations": 1, "storage": 1024, "default": True,
        "sort": 1,
    },
    {
        "code": "starter", "name": "Starter", "name_ar": "المبتدئ", "monthly": 999, "yearly": 9990,
        "trial_days": 14, "max_users": 10, "max_companies": 1, "max_branches": 3,
        "max_products": 5000, "max_integrations": 2, "storage": 5120, "default": False,
        "sort": 2,
    },
    {
        "code": "professional", "name": "Professional", "name_ar": "الاحترافي", "monthly": 2499, "yearly": 24990,
        "trial_days": 14, "max_users": 30, "max_companies": 3, "max_branches": 10,
        "max_products": 50000, "max_integrations": 10, "storage": 20480, "default": False,
        "sort": 3,
    },
)


def _rename_legacy_einvoice(bind, system_modules, plan_modules, tenant_modules) -> None:
    legacy = bind.execute(
        sa.select(system_modules.c.id).where(system_modules.c.code == "egyptian_einvoice")
    ).scalar_one_or_none()
    canonical = bind.execute(
        sa.select(system_modules.c.id).where(system_modules.c.code == "einvoice")
    ).scalar_one_or_none()
    if legacy is None or canonical is None or legacy == canonical:
        if legacy is not None and canonical is None:
            bind.execute(
                system_modules.update()
                .where(system_modules.c.id == legacy)
                .values(code="einvoice", name_en="Egyptian e-Invoice", name_ar="الفاتورة الإلكترونية المصرية")
            )
        return

    # Preserve existing references while eliminating the duplicate identity.
    for table in (plan_modules, tenant_modules):
        rows = bind.execute(
            sa.select(table.c.id, table.c.plan_id if hasattr(table.c, "plan_id") else table.c.tenant_id)
            .where(table.c.module_id == legacy)
        ).all()
        for row in rows:
            owner_column = table.c.plan_id if hasattr(table.c, "plan_id") else table.c.tenant_id
            owner_id = getattr(row, owner_column.name)
            duplicate = bind.execute(
                sa.select(table.c.id).where(owner_column == owner_id, table.c.module_id == canonical)
            ).scalar_one_or_none()
            if duplicate is None:
                bind.execute(table.update().where(table.c.id == row.id).values(module_id=canonical))
            else:
                bind.execute(table.delete().where(table.c.id == row.id))
    bind.execute(system_modules.delete().where(system_modules.c.id == legacy))


def _ensure_module(bind, system_modules, code, name_en, name_ar, is_core, display_order):
    existing = bind.execute(
        sa.select(system_modules.c.id).where(system_modules.c.code == code)
    ).scalar_one_or_none()
    values = {
        "code": code,
        "name_en": name_en,
        "name_ar": name_ar,
        "description_en": f"PrimeERP module: {name_en}.",
        "description_ar": f"وحدة {name_ar} في منصة PrimeERP.",
        "is_core": is_core,
        "is_active": True,
        "display_order": display_order,
    }
    if existing is None:
        return bind.execute(system_modules.insert().values(**values).returning(system_modules.c.id)).scalar_one()
    bind.execute(system_modules.update().where(system_modules.c.id == existing).values(**values))
    return existing


def _ensure_plan(bind, plans, legacy_plans, spec):
    now = datetime.now(timezone.utc)
    canonical = bind.execute(
        sa.select(plans.c.id).where(plans.c.code == spec["code"], plans.c.version == 1, plans.c.is_deleted.is_(False))
    ).scalar_one_or_none()
    legacy = bind.execute(
        sa.select(legacy_plans.c.id).where(legacy_plans.c.code == spec["code"])
    ).scalar_one_or_none()

    if canonical is not None and legacy is not None and canonical != legacy:
        raise RuntimeError(
            f"Plan identity conflict for {spec['code']}: plans.id={canonical}, subscription_plans.id={legacy}. "
            "Resolve the conflicting IDs before upgrading."
        )

    if canonical is None:
        values = {
            "code": spec["code"], "version": 1, "name": spec["name"], "name_ar": spec["name_ar"],
            "display_name": spec["name"], "description": f"PrimeERP {spec['name']} plan",
            "monthly_price": spec["monthly"], "yearly_price": spec["yearly"], "currency": "EGP",
            "billing_cycle": "monthly", "trial_days": spec["trial_days"], "grace_period_days": 7,
            "effective_from": now, "effective_to": None, "is_default": spec["default"], "is_public": True,
            "is_free": spec["monthly"] == 0 and spec["yearly"] == 0, "is_custom": False,
            "status": "active", "plan_type": "standard", "sort_order": spec["sort"],
            "uuid": str(uuid4()), "created_at": now, "updated_at": now, "is_deleted": False,
            "deleted_at": None, "deleted_by": None, "max_users": spec["max_users"],
            "max_companies": spec["max_companies"], "max_branches": spec["max_branches"],
            "max_products": spec["max_products"], "max_integrations": spec["max_integrations"],
            "storage_limit_mb": spec["storage"],
        }
        canonical = bind.execute(plans.insert().values(**values).returning(plans.c.id)).scalar_one()

    if legacy is None:
        values = {
            "id": canonical, "name_ar": spec["name_ar"], "name_en": spec["name"], "code": spec["code"],
            "description_ar": f"خطة {spec['name_ar']} في PrimeERP.", "description_en": f"PrimeERP {spec['name']} plan",
            "monthly_price": spec["monthly"], "yearly_price": spec["yearly"], "currency_code": "EGP",
            "trial_days": spec["trial_days"], "max_users": spec["max_users"], "max_companies": spec["max_companies"],
            "max_branches": spec["max_branches"], "max_products": spec["max_products"],
            "max_integrations": spec["max_integrations"], "storage_limit_mb": spec["storage"],
            "is_public": True, "is_active": True, "display_order": spec["sort"],
        }
        bind.execute(legacy_plans.insert().values(**values))
    return canonical


def upgrade() -> None:
    bind = op.get_bind()
    metadata = sa.MetaData()
    system_modules = sa.Table("system_modules", metadata, autoload_with=bind)
    plan_modules = sa.Table("plan_modules", metadata, autoload_with=bind)
    tenant_modules = sa.Table("tenant_modules", metadata, autoload_with=bind)
    plans = sa.Table("plans", metadata, autoload_with=bind)
    legacy_plans = sa.Table("subscription_plans", metadata, autoload_with=bind)

    _rename_legacy_einvoice(bind, system_modules, plan_modules, tenant_modules)

    module_ids = {
        code: _ensure_module(bind, system_modules, code, name_en, name_ar, is_core, display_order)
        for code, name_en, name_ar, is_core, display_order in MODULES
    }

    plan_ids = {spec["code"]: _ensure_plan(bind, plans, legacy_plans, spec) for spec in PLANS}

    # Exact entitlement matrix for the release plans. Existing rows outside the
    # matrix are disabled rather than deleted, preserving audit/history.
    for plan_code, plan_id in plan_ids.items():
        enabled = PLAN_ENTITLEMENTS[plan_code]
        for code, module_id in module_ids.items():
            existing = bind.execute(
                sa.select(plan_modules.c.id).where(
                    plan_modules.c.plan_id == plan_id,
                    plan_modules.c.module_id == module_id,
                )
            ).scalar_one_or_none()
            if existing is None:
                bind.execute(plan_modules.insert().values(plan_id=plan_id, module_id=module_id, is_enabled=code in enabled))
            else:
                bind.execute(plan_modules.update().where(plan_modules.c.id == existing).values(is_enabled=code in enabled))

    # Explicitly synchronize the legacy sequence after deterministic ID mirroring.
    bind.execute(sa.text("SELECT setval(pg_get_serial_sequence('subscription_plans','id'), COALESCE((SELECT MAX(id) FROM subscription_plans), 1), true)"))


def downgrade() -> None:
    # Release catalog data is intentionally retained; subscriptions may already
    # reference these plans/modules.
    pass
