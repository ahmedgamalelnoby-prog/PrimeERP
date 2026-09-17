from __future__ import annotations

from calendar import monthrange
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.platform.plans.constants import PlanStatus
from app.modules.platform.plans.models import Plan
from app.modules.saas.models import PlanModule, Subscription, SubscriptionPlan, SystemModule, Tenant, TenantModule

ACTIVE_STATUSES = ("trialing", "active", "past_due", "grace")
BILLING_CYCLES = ("monthly", "yearly")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _tenant(db: Session, tenant_id: int) -> Tenant:
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return tenant


def _reject_suspended(tenant: Tenant) -> None:
    if tenant.status == "suspended" or not tenant.is_active:
        raise HTTPException(status_code=423, detail="Tenant requires explicit reactivation before subscription lifecycle changes")


def _canonical_plan(db: Session, plan_id: int) -> Plan:
    plan = db.scalar(select(Plan).where(
        Plan.id == plan_id,
        Plan.is_deleted.is_(False),
        Plan.status == PlanStatus.ACTIVE.value,
    ))
    if plan is None:
        raise HTTPException(status_code=404, detail="Canonical subscription plan is not active")
    return plan


def _canonical_plan_by_code(db: Session, code: str, version: int = 1) -> Plan:
    plan = db.scalar(select(Plan).where(
        Plan.code == code.strip().lower(),
        Plan.version == version,
        Plan.is_deleted.is_(False),
        Plan.status == PlanStatus.ACTIVE.value,
    ))
    if plan is None:
        raise HTTPException(status_code=503, detail=f"Canonical plan '{code}' is not configured")
    return plan


def _legacy_plan(db: Session, canonical: Plan) -> SubscriptionPlan:
    legacy = db.scalar(select(SubscriptionPlan).where(SubscriptionPlan.code == canonical.code).with_for_update())
    if legacy is not None and legacy.id != canonical.id:
        raise HTTPException(status_code=500, detail=f"Plan identity mismatch for '{canonical.code}'")
    if legacy is None:
        legacy = SubscriptionPlan(
            id=canonical.id,
            name_ar=canonical.name_ar or canonical.name,
            name_en=canonical.display_name or canonical.name,
            code=canonical.code,
            description_ar=canonical.description,
            description_en=canonical.description,
            monthly_price=canonical.monthly_price,
            yearly_price=canonical.yearly_price,
            currency_code=canonical.currency,
            trial_days=canonical.trial_days,
            max_users=canonical.max_users or 5,
            max_companies=canonical.max_companies or 1,
            max_branches=canonical.max_branches or 1,
            max_products=canonical.max_products or 1000,
            max_integrations=canonical.max_integrations or 0,
            storage_limit_mb=canonical.storage_limit_mb or 1024,
            is_public=canonical.is_public,
            is_active=True,
            display_order=canonical.sort_order,
        )
        db.add(legacy)
        db.flush()
    return legacy


def resolve_legacy_plan(db: Session, code: str, version: int = 1) -> SubscriptionPlan:
    return _legacy_plan(db, _canonical_plan_by_code(db, code, version))


def _active_subscription(db: Session, tenant_id: int, now: datetime) -> Subscription | None:
    return db.scalar(select(Subscription).where(
        Subscription.tenant_id == tenant_id,
        Subscription.status.in_(ACTIVE_STATUSES),
        Subscription.starts_at <= now,
        (Subscription.ends_at.is_(None)) | (Subscription.ends_at > now),
    ).order_by(Subscription.ends_at.desc().nullslast(), Subscription.id.desc()))


def _period_end(start: datetime, billing_cycle: str) -> datetime:
    if billing_cycle not in BILLING_CYCLES:
        raise HTTPException(status_code=422, detail="Billing cycle must be monthly or yearly")
    months = 1 if billing_cycle == "monthly" else 12
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start.day, monthrange(year, month)[1])
    return start.replace(year=year, month=month, day=day)


def _provision_plan_modules(
    db: Session,
    tenant_id: int,
    legacy_plan: SubscriptionPlan,
    starts_at: datetime,
    ends_at: datetime | None,
    allowed_module_codes: set[str] | None = None,
) -> list[SystemModule]:
    modules = list(db.scalars(select(SystemModule).join(PlanModule, PlanModule.module_id == SystemModule.id).where(
        PlanModule.plan_id == legacy_plan.id,
        PlanModule.is_enabled.is_(True),
        SystemModule.is_active.is_(True),
    )).all())
    if allowed_module_codes is not None:
        modules = [module for module in modules if module.is_core or module.code in allowed_module_codes]

    selected_module_ids = {module.id for module in modules}
    plan_grants = db.scalars(select(TenantModule).where(
        TenantModule.tenant_id == tenant_id,
        TenantModule.source == "plan",
    )).all()
    for grant in plan_grants:
        if grant.module_id not in selected_module_ids:
            grant.is_enabled = False
            grant.starts_at = starts_at
            grant.ends_at = ends_at

    for module in modules:
        grant = db.scalar(select(TenantModule).where(
            TenantModule.tenant_id == tenant_id,
            TenantModule.module_id == module.id,
        ))
        if grant is None:
            db.add(TenantModule(
                tenant_id=tenant_id,
                module_id=module.id,
                is_enabled=True,
                source="plan",
                starts_at=starts_at,
                ends_at=ends_at,
            ))
        elif grant.source == "plan":
            grant.is_enabled = True
            grant.starts_at = starts_at
            grant.ends_at = ends_at
        # Explicit overrides are intentionally authoritative and are never
        # rewritten by a plan transition.
    return modules


def create_trial(
    db: Session,
    tenant_id: int,
    plan_code: str = "trial",
    plan_version: int = 1,
    starts_at: datetime | None = None,
    allowed_module_codes: set[str] | None = None,
) -> tuple[Subscription, Plan, list[SystemModule]]:
    tenant = _tenant(db, tenant_id)
    _reject_suspended(tenant)
    canonical = _canonical_plan_by_code(db, plan_code, plan_version)
    legacy = _legacy_plan(db, canonical)
    start = starts_at or _now()
    end = start + timedelta(days=canonical.trial_days)
    existing = _active_subscription(db, tenant_id, start)
    if existing is not None:
        raise HTTPException(status_code=409, detail="Tenant already has an active subscription")
    subscription = Subscription(
        tenant_id=tenant_id,
        plan_id=legacy.id,
        status="trialing",
        billing_cycle=canonical.billing_cycle,
        starts_at=start,
        ends_at=end,
        trial_ends_at=end,
        next_billing_date=None,
        is_auto_renew=False,
    )
    db.add(subscription)
    db.flush()
    modules = _provision_plan_modules(db, tenant_id, legacy, start, end, allowed_module_codes=allowed_module_codes)
    tenant.status = "trial"
    tenant.is_trial = True
    tenant.trial_started_at = start
    tenant.trial_ends_at = end
    tenant.is_active = True
    return subscription, canonical, modules


def convert_trial_to_paid(db: Session, tenant_id: int, plan_id: int, billing_cycle: str = "monthly", auto_renew: bool = True) -> Subscription:
    tenant = _tenant(db, tenant_id)
    _reject_suspended(tenant)
    canonical = _canonical_plan(db, plan_id)
    legacy = _legacy_plan(db, canonical)
    now = _now()
    current = _active_subscription(db, tenant_id, now)
    if current is not None and current.status == "active" and current.plan_id == legacy.id:
        raise HTTPException(status_code=409, detail="Tenant already has this paid plan")
    if current is not None and current.status == "active":
        raise HTTPException(status_code=409, detail="Tenant already has an active paid subscription")
    subscription = current if current is not None and current.status == "trialing" else None
    if subscription is None:
        subscription = Subscription(tenant_id=tenant.id)
        db.add(subscription)
    subscription.plan_id = legacy.id
    subscription.status = "active"
    subscription.billing_cycle = billing_cycle
    subscription.starts_at = now
    subscription.ends_at = _period_end(now, billing_cycle)
    subscription.trial_ends_at = None
    subscription.next_billing_date = subscription.ends_at if auto_renew else None
    subscription.cancelled_at = None
    subscription.is_auto_renew = auto_renew
    tenant.status = "active"
    tenant.is_trial = False
    tenant.is_active = True
    tenant.trial_ends_at = None
    tenant.suspended_at = None
    tenant.suspension_reason = None
    _provision_plan_modules(db, tenant_id, legacy, now, subscription.ends_at)
    db.commit()
    db.refresh(subscription)
    return subscription


def renew_subscription(db: Session, tenant_id: int, plan_id: int | None = None, billing_cycle: str | None = None) -> Subscription:
    tenant = _tenant(db, tenant_id)
    _reject_suspended(tenant)
    now = _now()
    current = _active_subscription(db, tenant_id, now)
    if current is None:
        current = db.scalar(select(Subscription).where(Subscription.tenant_id == tenant_id).order_by(Subscription.ends_at.desc().nullslast(), Subscription.id.desc()))
    if current is None:
        raise HTTPException(status_code=404, detail="No subscription exists for tenant")
    canonical = _canonical_plan(db, plan_id if plan_id is not None else current.plan_id)
    legacy = _legacy_plan(db, canonical)
    cycle = billing_cycle or current.billing_cycle
    start = current.ends_at if current.ends_at and current.ends_at > now else now
    current.plan_id = legacy.id
    current.status = "active"
    current.billing_cycle = cycle
    current.starts_at = start
    current.ends_at = _period_end(start, cycle)
    current.trial_ends_at = None
    current.cancelled_at = None
    current.next_billing_date = current.ends_at if current.is_auto_renew else None
    tenant.status = "active"
    tenant.is_trial = False
    tenant.is_active = True
    _provision_plan_modules(db, tenant_id, legacy, start, current.ends_at)
    db.commit()
    db.refresh(current)
    return current


def cancel_auto_renewal(db: Session, tenant_id: int) -> Subscription:
    tenant = _tenant(db, tenant_id)
    _reject_suspended(tenant)
    subscription = _active_subscription(db, tenant_id, _now())
    if subscription is None:
        raise HTTPException(status_code=404, detail="No active subscription exists for tenant")
    subscription.is_auto_renew = False
    subscription.next_billing_date = None
    subscription.cancelled_at = _now()
    db.commit()
    db.refresh(subscription)
    return subscription


def suspend_tenant(db: Session, tenant_id: int, reason: str) -> Tenant:
    tenant = _tenant(db, tenant_id)
    reason = reason.strip()
    if not reason:
        raise HTTPException(status_code=422, detail="Suspension reason is required")
    tenant.status = "suspended"
    tenant.is_active = False
    tenant.suspended_at = _now()
    tenant.suspension_reason = reason
    db.commit()
    db.refresh(tenant)
    return tenant


def unsuspend_tenant(db: Session, tenant_id: int) -> Tenant:
    tenant = _tenant(db, tenant_id)
    subscription = _active_subscription(db, tenant_id, _now())
    if subscription is None:
        raise HTTPException(status_code=409, detail="Tenant has no valid subscription for reactivation")
    tenant.status = "trial" if subscription.status == "trialing" else "active"
    tenant.is_active = True
    tenant.is_trial = subscription.status == "trialing"
    tenant.trial_ends_at = subscription.trial_ends_at if subscription.status == "trialing" else None
    tenant.suspended_at = None
    tenant.suspension_reason = None
    db.commit()
    db.refresh(tenant)
    return tenant


def expire_due_subscriptions(db: Session, now: datetime | None = None) -> int:
    current = now or _now()
    subscriptions = db.scalars(select(Subscription).where(
        Subscription.status.in_(("trialing", "active", "past_due", "grace")),
        Subscription.ends_at.is_not(None),
        Subscription.ends_at <= current,
    ).with_for_update()).all()
    changed = 0
    for subscription in subscriptions:
        canonical = db.get(Plan, subscription.plan_id)
        grace_days = canonical.grace_period_days if canonical is not None else 0
        tenant = db.get(Tenant, subscription.tenant_id)
        grace_end = subscription.ends_at + timedelta(days=grace_days)
        if current < grace_end:
            subscription.status = "grace"
            if tenant is not None:
                tenant.status = "grace"
                tenant.is_active = True
        else:
            subscription.status = "expired"
            subscription.next_billing_date = None
            if tenant is not None:
                tenant.status = "expired"
                tenant.is_active = False
        changed += 1
    db.commit()
    return changed