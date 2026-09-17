from collections.abc import Callable
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.core.module_engine.identity import canonical_business_code
from app.database.session import get_db
from app.modules.branches.models import Branch
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.inventory.items.models import InventoryItem
from app.modules.platform.plans.constants import PlanStatus
from app.modules.platform.plans.models import Plan
from app.modules.saas.models import PlanModule, Subscription, SystemModule, Tenant, TenantModule

CORE_MODULES = {"dashboard", "users", "companies", "branches"}
ACTIVE_SUBSCRIPTION_STATUSES = ("trialing", "active", "past_due", "grace")


def _active_subscription(db: Session, tenant_id: int) -> Subscription | None:
    now = datetime.now(timezone.utc)
    return db.scalar(
        select(Subscription)
        .join(Plan, Plan.id == Subscription.plan_id)
        .join(Tenant, Tenant.id == Subscription.tenant_id)
        .where(
            Subscription.tenant_id == tenant_id,
            Tenant.is_active.is_(True),
            text("tenants.status <> 'suspended'"),
            Subscription.status.in_(ACTIVE_SUBSCRIPTION_STATUSES),
            Subscription.starts_at <= now,
            or_(Subscription.ends_at.is_(None), Subscription.ends_at > now),
            Plan.is_deleted.is_(False),
            Plan.status == PlanStatus.ACTIVE.value,
        )
        .order_by(Subscription.ends_at.desc().nullslast(), Subscription.id.desc())
    )


def tenant_has_module(db: Session, tenant_id: int, module_code: str) -> bool:
    """Check a business-level entitlement using one canonical module identity."""
    subscription = _active_subscription(db, tenant_id)
    if subscription is None:
        return False

    module_code = canonical_business_code(module_code)
    if module_code in CORE_MODULES:
        return True

    module = db.scalar(
        select(SystemModule).where(
            SystemModule.code == module_code,
            SystemModule.is_active.is_(True),
        )
    )
    if module is None:
        return False

    override = db.scalar(
        select(TenantModule).where(
            TenantModule.tenant_id == tenant_id,
            TenantModule.module_id == module.id,
            TenantModule.source == "override",
        )
    )
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
    canonical_code = canonical_business_code(module_code)

    def dependency(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> User:
        tenant_id = get_effective_tenant_id(current_user)
        if not tenant_has_module(db, tenant_id, canonical_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Module '{canonical_code}' is not enabled for this subscription",
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
    plan = db.get(Plan, subscription.plan_id)
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
