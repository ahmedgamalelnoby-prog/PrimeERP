from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.saas.models import Subscription, SubscriptionPlan, Tenant

ACTIVE_STATUSES = ("trialing", "active", "past_due")
BILLING_CYCLES = {"monthly": 30, "yearly": 365}


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


def _plan(db: Session, plan_id: int) -> SubscriptionPlan:
    plan = db.get(SubscriptionPlan, plan_id)
    if plan is None or not plan.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription plan is not active")
    return plan


def _active_subscription(db: Session, tenant_id: int, now: datetime) -> Subscription | None:
    return db.scalar(
        select(Subscription).where(
            Subscription.tenant_id == tenant_id,
            Subscription.status.in_(ACTIVE_STATUSES),
            Subscription.starts_at <= now,
            (Subscription.ends_at.is_(None)) | (Subscription.ends_at > now),
        ).order_by(Subscription.ends_at.desc().nullslast(), Subscription.id.desc())
    )


def _period_end(start: datetime, billing_cycle: str) -> datetime:
    days = BILLING_CYCLES.get(billing_cycle)
    if days is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Billing cycle must be monthly or yearly")
    return start + timedelta(days=days)


def convert_trial_to_paid(db: Session, tenant_id: int, plan_id: int, billing_cycle: str = "monthly", auto_renew: bool = True) -> Subscription:
    tenant = _tenant(db, tenant_id)
    _reject_suspended(tenant)
    plan = _plan(db, plan_id)
    now = _now()
    if billing_cycle not in BILLING_CYCLES:
        raise HTTPException(status_code=422, detail="Billing cycle must be monthly or yearly")
    current = _active_subscription(db, tenant_id, now)
    if current is not None and current.status == "active" and current.plan_id == plan.id:
        raise HTTPException(status_code=409, detail="Tenant already has this paid plan")
    if current is not None and current.status == "active":
        raise HTTPException(status_code=409, detail="Tenant already has an active paid subscription")
    subscription = current if current is not None and current.status == "trialing" else None
    if subscription is None:
        subscription = Subscription(tenant_id=tenant.id)
        db.add(subscription)
    subscription.plan_id = plan.id
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
    plan = _plan(db, plan_id if plan_id is not None else current.plan_id)
    cycle = billing_cycle or current.billing_cycle
    if cycle not in BILLING_CYCLES:
        raise HTTPException(status_code=422, detail="Billing cycle must be monthly or yearly")
    start = current.ends_at if current.ends_at and current.ends_at > now else now
    current.plan_id = plan.id
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
    db.commit()
    db.refresh(current)
    return current


def cancel_auto_renewal(db: Session, tenant_id: int) -> Subscription:
    tenant = _tenant(db, tenant_id)
    _reject_suspended(tenant)
    now = _now()
    subscription = _active_subscription(db, tenant_id, now)
    if subscription is None:
        raise HTTPException(status_code=404, detail="No active subscription exists for tenant")
    subscription.is_auto_renew = False
    subscription.next_billing_date = None
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
    now = _now()
    subscription = _active_subscription(db, tenant_id, now)
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
