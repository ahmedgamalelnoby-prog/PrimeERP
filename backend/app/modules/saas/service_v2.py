from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.modules.branches.models import Branch
from app.modules.companies.models import Company
from app.modules.identity.models import User
from app.modules.saas.models import PlanModule, Subscription, SubscriptionPlan, SystemModule, Tenant, TenantModule
from app.modules.saas.schemas import TenantRegistrationRequest


def generate_slug(db: Session, business_name: str) -> str:
    normalized = unicodedata.normalize("NFKD", business_name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    base = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_name.lower()).strip("-")[:80] or "tenant"
    slug = base
    counter = 1
    while db.query(Tenant.id).filter(Tenant.slug == slug).first() is not None:
        counter += 1
        slug = f"{base[:70]}-{counter}"
    return slug


def get_trial_plan(db: Session) -> SubscriptionPlan:
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.code == "trial",
        SubscriptionPlan.is_active.is_(True),
    ).first()
    if plan is None:
        raise HTTPException(status_code=503, detail="Trial subscription plan is not configured")
    setting = db.execute(text("SELECT value FROM platform_settings WHERE key='default_trial_days' LIMIT 1")).scalar_one_or_none()
    if setting is not None:
        try:
            plan.trial_days = max(1, min(365, int(setting)))
        except (TypeError, ValueError):
            pass
    return plan


def validate_registration_uniqueness(db: Session, payload: TenantRegistrationRequest) -> None:
    email = str(payload.email).strip().lower()
    if db.query(User.id).filter(func.lower(User.email) == email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    if db.query(User.id).filter(func.lower(User.username) == payload.username.lower()).first():
        raise HTTPException(status_code=409, detail="This username is already in use")


def resolve_enabled_modules(db: Session, plan: SubscriptionPlan) -> list[SystemModule]:
    return db.query(SystemModule).join(PlanModule, PlanModule.module_id == SystemModule.id).filter(
        PlanModule.plan_id == plan.id,
        PlanModule.is_enabled.is_(True),
        SystemModule.is_active.is_(True),
    ).order_by(SystemModule.display_order.asc()).all()


def register_trial_tenant(db: Session, payload: TenantRegistrationRequest) -> dict:
    if len(payload.password.encode("utf-8")) > 72:
        raise HTTPException(status_code=422, detail="Password is too long. It must not exceed 72 bytes.")
    validate_registration_uniqueness(db, payload)
    trial_plan = get_trial_plan(db)
    now = datetime.now(timezone.utc)
    trial_ends_at = now + timedelta(days=trial_plan.trial_days or 14)
    email = str(payload.email).strip().lower()
    try:
        tenant = Tenant(
            name=payload.business_name, slug=generate_slug(db, payload.business_name),
            business_type=payload.business_type, owner_name=payload.owner_name,
            email=email, phone=payload.phone, country_code=payload.country_code,
            default_language=payload.language, default_locale="ar-EG" if payload.language == "ar" else "en-US",
            timezone="Africa/Cairo", currency_code="EGP", status="trial", is_trial=True,
            trial_started_at=now, trial_ends_at=trial_ends_at, is_active=True,
        )
        db.add(tenant); db.flush()
        company = Company(tenant_id=tenant.id, name=(payload.company_name or payload.business_name).strip(), code="MAIN", phone=payload.phone, email=email, is_active=True)
        db.add(company); db.flush()
        branch = Branch(tenant_id=tenant.id, company_id=company.id, name=(payload.branch_name or ("الفرع الرئيسي" if payload.language == "ar" else "Main Branch")).strip(), code="MAIN", phone=payload.phone, email=email, is_active=True)
        db.add(branch); db.flush()
        owner = User(
            tenant_id=tenant.id, username=payload.username, email=email, full_name=payload.owner_name,
            phone=payload.phone, hashed_password=get_password_hash(str(payload.password)),
            preferred_language=payload.language, is_active=True, is_superuser=True,
            is_platform_admin=False, is_deleted=False, must_change_password=False,
        )
        db.add(owner); db.flush()
        subscription = Subscription(
            tenant_id=tenant.id, plan_id=trial_plan.id, status="trialing", billing_cycle="monthly",
            starts_at=now, ends_at=trial_ends_at, trial_ends_at=trial_ends_at, is_auto_renew=False,
        )
        db.add(subscription); db.flush()
        modules = resolve_enabled_modules(db, trial_plan)
        for module in modules:
            db.add(TenantModule(tenant_id=tenant.id, module_id=module.id, is_enabled=True, starts_at=now, ends_at=trial_ends_at))
        db.commit()
        db.refresh(tenant); db.refresh(company); db.refresh(branch); db.refresh(owner); db.refresh(subscription)
        return {
            "message": "Trial account created successfully", "tenant": tenant, "company": company,
            "branch": branch, "user": owner, "subscription_status": subscription.status,
            "plan_code": trial_plan.code, "enabled_modules": [m.code for m in modules], "trial_ends_at": trial_ends_at,
        }
    except HTTPException:
        db.rollback(); raise
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="Registration database conflict") from exc
    except Exception as exc:
        db.rollback(); raise HTTPException(status_code=500, detail=f"Could not create trial account: {type(exc).__name__}") from exc
