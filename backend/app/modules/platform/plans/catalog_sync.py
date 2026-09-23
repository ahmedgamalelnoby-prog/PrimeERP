"""Synchronize the canonical platform plan catalog from the legacy SaaS plan catalog.

The application historically had two plan tables.  The canonical `plans` table is
now the platform-facing catalog, while tenant subscriptions still reference
`subscription_plans`.  This adapter keeps both representations aligned by code
so existing tenants and subscriptions continue to work without a destructive
migration.
"""

from sqlalchemy.orm import Session

from app.modules.platform.plans.models import Plan
from app.modules.saas.models import SubscriptionPlan


def _plan_type(code: str) -> str:
    return {
        "trial": "free",
        "starter": "standard",
        "professional": "professional",
        "enterprise": "enterprise",
        "custom": "custom",
    }.get(code, "standard")


def sync_canonical_plans(db: Session) -> list[Plan]:
    legacy_plans = (
        db.query(SubscriptionPlan)
        .order_by(SubscriptionPlan.display_order, SubscriptionPlan.id)
        .all()
    )
    if not legacy_plans:
        return []

    canonical_by_code = {
        plan.code: plan
        for plan in db.query(Plan)
        .filter(Plan.is_deleted.is_(False))
        .all()
    }

    default_code = "starter" if any(p.code == "starter" for p in legacy_plans) else legacy_plans[0].code
    changed = False

    for legacy in legacy_plans:
        canonical = canonical_by_code.get(legacy.code)
        if canonical is None:
            canonical = Plan(
                code=legacy.code,
                version=1,
                name=legacy.name_en,
                name_ar=legacy.name_ar,
                display_name=legacy.name_en,
                description=legacy.description_en or legacy.description_ar,
                monthly_price=legacy.monthly_price,
                yearly_price=legacy.yearly_price,
                currency=legacy.currency_code,
                billing_cycle="monthly",
                trial_days=legacy.trial_days,
                grace_period_days=7,
                max_users=legacy.max_users,
                max_companies=legacy.max_companies,
                max_branches=legacy.max_branches,
                max_products=legacy.max_products,
                max_integrations=legacy.max_integrations,
                storage_limit_mb=legacy.storage_limit_mb,
                is_default=legacy.code == default_code,
                is_public=legacy.is_public,
                is_free=legacy.monthly_price == 0,
                is_custom=legacy.code == "custom",
                status="active" if legacy.is_active else "inactive",
                plan_type=_plan_type(legacy.code),
                sort_order=legacy.display_order,
            )
            db.add(canonical)
            canonical_by_code[legacy.code] = canonical
            changed = True
            continue

        updates = {
            "name": legacy.name_en,
            "name_ar": legacy.name_ar,
            "display_name": legacy.name_en,
            "description": legacy.description_en or legacy.description_ar,
            "monthly_price": legacy.monthly_price,
            "yearly_price": legacy.yearly_price,
            "currency": legacy.currency_code,
            "trial_days": legacy.trial_days,
            "max_users": legacy.max_users,
            "max_companies": legacy.max_companies,
            "max_branches": legacy.max_branches,
            "max_products": legacy.max_products,
            "max_integrations": legacy.max_integrations,
            "storage_limit_mb": legacy.storage_limit_mb,
            "is_public": legacy.is_public,
            "is_free": legacy.monthly_price == 0,
            "is_custom": legacy.code == "custom",
            "status": "active" if legacy.is_active else "inactive",
            "plan_type": _plan_type(legacy.code),
            "sort_order": legacy.display_order,
        }
        for field, value in updates.items():
            if getattr(canonical, field) != value:
                setattr(canonical, field, value)
                changed = True

    # Clear existing defaults first. PostgreSQL enforces a partial unique
    # index, so changing the default in one pass can otherwise create a
    # transient two-default conflict.
    for canonical in canonical_by_code.values():
        if canonical.is_default:
            canonical.is_default = False
            changed = True

    canonical_default = canonical_by_code.get(default_code)
    if canonical_default is not None:
        canonical_default.is_default = True
        changed = True

    if changed:
        db.flush()

    return sorted(canonical_by_code.values(), key=lambda p: (p.sort_order, p.name))
