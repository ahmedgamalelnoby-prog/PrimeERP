from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.branches.models import Branch
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.saas.models import PlanModule, Subscription, SubscriptionPlan, SystemModule, TenantModule


CORE_MODULES = {"dashboard", "users", "companies", "branches"}


def _active_subscription(db: Session, tenant_id: int) -> Subscription | None:
    return db.scalar(
        select(Subscription)
        .join(SubscriptionPlan, SubscriptionPlan.id == Subscription.plan_id)
        .where(
            Subscription.tenant_id == tenant_id,
            Subscription.status.in_(("trialing", "active", "past_due")),
            SubscriptionPlan.is_active.is_(True),
        )
        .order_by(Subscription.ends_at.desc().nullslast(), Subscription.id.desc())
    )


def tenant_has_module(db: Session, tenant_id: int, module_code: str) -> bool:
    if module_code in CORE_MODULES:
        return True
    subscription = _active_subscription(db, tenant_id)
    if subscription is None:
        return False
    module = db.scalar(select(SystemModule).where(SystemModule.code == module_code, SystemModule.is_active.is_(True)))
    if module is None:
        return False
    tenant_override = db.scalar(
        select(TenantModule).where(
            TenantModule.tenant_id == tenant_id,
            TenantModule.module_id == module.id,
        )
    )
    if tenant_override is not None:
        if not tenant_override.is_enabled:
            return False
        if tenant_override.starts_at is not None and tenant_override.starts_at > subscription.starts_at:
            # The subscription itself is still active; the module starts only at its configured date.
            from datetime import datetime, timezone
            if tenant_override.starts_at > datetime.now(timezone.utc):
                return False
        if tenant_override.ends_at is not None:
            from datetime import datetime, timezone
            if tenant_override.ends_at <= datetime.now(timezone.utc):
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
        if current_user.is_platform_admin:
            return current_user
        if current_user.tenant_id is None:
            raise HTTPException(status_code=403, detail="User is not assigned to a tenant")
        if not tenant_has_module(db, current_user.tenant_id, module_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Module '{module_code}' is not enabled for this subscription",
            )
        return current_user

    return dependency


def _limit_for(db: Session, tenant_id: int, field: str) -> int | None:
    subscription = _active_subscription(db, tenant_id)
    if subscription is None:
        return None
    custom = getattr(subscription, f"custom_{field}", None)
    if custom is not None:
        return custom
    plan = db.get(SubscriptionPlan, subscription.plan_id)
    return getattr(plan, f"max_{field}", None) if plan else None


def enforce_user_limit(db: Session, tenant_id: int) -> None:
    limit = _limit_for(db, tenant_id, "max_users")
    if limit is None:
        return
    current = db.scalar(select(func.count(User.id)).where(User.tenant_id == tenant_id, User.is_deleted.is_(False))) or 0
    if current >= limit:
        raise HTTPException(status_code=409, detail=f"User limit reached ({limit})")


def enforce_company_limit(db: Session, tenant_id: int) -> None:
    limit = _limit_for(db, tenant_id, "max_companies")
    if limit is None:
        return
    current = db.scalar(select(func.count(Company.id)).where(Company.tenant_id == tenant_id, Company.is_active.is_(True))) or 0
    if current >= limit:
        raise HTTPException(status_code=409, detail=f"Company limit reached ({limit})")


def enforce_branch_limit(db: Session, tenant_id: int) -> None:
    limit = _limit_for(db, tenant_id, "max_branches")
    if limit is None:
        return
    current = db.scalar(select(func.count(Branch.id)).where(Branch.tenant_id == tenant_id, Branch.is_active.is_(True))) or 0
    if current >= limit:
        raise HTTPException(status_code=409, detail=f"Branch limit reached ({limit})")
