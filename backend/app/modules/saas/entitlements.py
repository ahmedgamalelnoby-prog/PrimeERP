from collections.abc import Callable
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.database.session import get_db
from app.modules.branches.models import Branch
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.inventory.items.models import InventoryItem
from app.modules.saas.models import PlanModule, Subscription, SubscriptionPlan, SystemModule, Tenant, TenantModule

CORE_MODULES = {"dashboard", "users", "companies", "branches"}
TRIAL_BUSINESS_MODULES: dict[str, set[str]] = {
    "restaurant": {"dashboard","users","companies","branches","accounting","sales","inventory","purchasing","restaurant","pos","reports"},
    "cafe": {"dashboard","users","companies","branches","accounting","sales","inventory","purchasing","restaurant","pos","reports"},
    "retail": {"dashboard","users","companies","branches","accounting","sales","inventory","purchasing","crm","pos","shipping","reports"},
    "fashion": {"dashboard","users","companies","branches","accounting","sales","inventory","purchasing","crm","pos","shipping","reports"},
    "perfume": {"dashboard","users","companies","branches","accounting","sales","inventory","purchasing","crm","pos","manufacturing","shipping","reports"},
    "manufacturing": {"dashboard","users","companies","branches","accounting","sales","inventory","purchasing","manufacturing","reports"},
    "supermarket": {"dashboard","users","companies","branches","accounting","sales","inventory","purchasing","pos","crm","shipping","reports"},
    "pharmacy": {"dashboard","users","companies","branches","accounting","sales","inventory","purchasing","reports"},
    "services": {"dashboard","users","companies","branches","accounting","sales","crm","reports"},
    "other": {"dashboard","users","companies","branches","accounting","reports"},
}



def _active_subscription(db: Session, tenant_id: int) -> Subscription | None:
    now = datetime.now(timezone.utc)
    return db.scalar(
        select(Subscription)
        .join(SubscriptionPlan, SubscriptionPlan.id == Subscription.plan_id)
        .join(Tenant, Tenant.id == Subscription.tenant_id)
        .where(
            Subscription.tenant_id == tenant_id,
            Tenant.is_active.is_(True),
            text("tenants.status <> 'suspended'"),
            Subscription.status.in_(("trialing", "active", "past_due")),
            Subscription.starts_at <= now,
            or_(Subscription.ends_at.is_(None), Subscription.ends_at > now),
            SubscriptionPlan.is_active.is_(True),
        )
        .order_by(Subscription.ends_at.desc().nullslast(), Subscription.id.desc())
    )


def tenant_has_module(db: Session, tenant_id: int, module_code: str) -> bool:
    subscription = _active_subscription(db, tenant_id)
    if subscription is None:
        return False
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        return False
    if module_code in CORE_MODULES:
        return True
    if tenant.is_trial:
        allowed_codes = TRIAL_BUSINESS_MODULES.get(tenant.business_type, TRIAL_BUSINESS_MODULES["other"])
        if module_code not in allowed_codes:
            return False
    module = db.scalar(select(SystemModule).where(SystemModule.code == module_code, SystemModule.is_active.is_(True)))
    if module is None:
        return False
    override = db.scalar(select(TenantModule).where(TenantModule.tenant_id == tenant_id, TenantModule.module_id == module.id))
    now = datetime.now(timezone.utc)
    if override is not None:
        if not override.is_enabled:
            return False
        if override.starts_at is not None and override.starts_at > now:
            return False
        if override.ends_at is not None and override.ends_at <= now:
            return False
        return True
    return db.scalar(
        select(PlanModule.id).where(
            PlanModule.plan_id == subscription.plan_id,
            PlanModule.module_id == module.id,
            PlanModule.is_enabled.is_(True),
        )
    ) is not None


def require_module(module_code: str) -> Callable:
    def dependency(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> User:
        tenant_id = get_effective_tenant_id(current_user)
        if not tenant_has_module(db, tenant_id, module_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Module '{module_code}' is not enabled for this subscription",
            )
        return current_user

    return dependency


def _limit_for(db: Session, tenant_id: int, resource: str) -> int | None:
    subscription = _active_subscription(db, tenant_id)
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="An active subscription is required for this operation",
        )
    custom = getattr(subscription, f"custom_max_{resource}", None)
    if custom is not None:
        return custom
    plan = db.get(SubscriptionPlan, subscription.plan_id)
    return getattr(plan, f"max_{resource}", None) if plan else None


def enforce_user_limit(db: Session, tenant_id: int) -> None:
    limit = _limit_for(db, tenant_id, "users")
    if limit is None:
        return
    current = db.scalar(select(func.count(User.id)).where(User.tenant_id == tenant_id, User.is_deleted.is_(False))) or 0
    if current >= limit:
        raise HTTPException(status_code=409, detail=f"User limit reached ({limit})")


def enforce_company_limit(db: Session, tenant_id: int) -> None:
    limit = _limit_for(db, tenant_id, "companies")
    if limit is None:
        return
    current = db.scalar(select(func.count(Company.id)).where(Company.tenant_id == tenant_id, Company.is_active.is_(True))) or 0
    if current >= limit:
        raise HTTPException(status_code=409, detail=f"Company limit reached ({limit})")


def enforce_branch_limit(db: Session, tenant_id: int) -> None:
    limit = _limit_for(db, tenant_id, "branches")
    if limit is None:
        return
    current = db.scalar(select(func.count(Branch.id)).where(Branch.tenant_id == tenant_id, Branch.is_active.is_(True))) or 0
    if current >= limit:
        raise HTTPException(status_code=409, detail=f"Branch limit reached ({limit})")


def enforce_product_limit(db: Session, tenant_id: int, company_id: int) -> None:
    """Enforce max_products across the whole tenant, not per company."""
    limit = _limit_for(db, tenant_id, "products")
    if limit is None:
        return
    current = db.scalar(
        select(func.count(InventoryItem.id))
        .join(Company, Company.id == InventoryItem.company_id)
        .where(Company.tenant_id == tenant_id, InventoryItem.is_active.is_(True))
    ) or 0
    if current >= limit:
        raise HTTPException(status_code=409, detail=f"Product limit reached ({limit})")
