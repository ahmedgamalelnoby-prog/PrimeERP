import logging
import re
import unicodedata

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)

from app.core.security import get_password_hash
from app.modules.identity.models import User
from app.modules.branches.models import Branch
from app.modules.companies.models import Company
from app.modules.roles.models import Role
from app.modules.saas.models import (
    PlanModule,
    Subscription,
    SubscriptionPlan,
    SystemModule,
    Tenant,
    TenantModule,
)
from app.modules.saas.schemas import TenantRegistrationRequest


BUSINESS_MODULES: dict[str, set[str]] = {
    "restaurant": {"dashboard", "users", "companies", "branches", "accounting", "sales", "inventory", "purchasing", "restaurant", "pos", "reports"},
    "cafe": {"dashboard", "users", "companies", "branches", "accounting", "sales", "inventory", "purchasing", "restaurant", "pos", "reports"},
    "retail": {"dashboard", "users", "companies", "branches", "accounting", "sales", "inventory", "purchasing", "crm", "pos", "shipping", "reports"},
    "fashion": {"dashboard", "users", "companies", "branches", "accounting", "sales", "inventory", "purchasing", "crm", "pos", "shipping", "reports"},
    "perfume": {"dashboard", "users", "companies", "branches", "accounting", "sales", "inventory", "purchasing", "crm", "pos", "manufacturing", "shipping", "reports"},
    "manufacturing": {"dashboard", "users", "companies", "branches", "accounting", "sales", "inventory", "purchasing", "manufacturing", "reports"},
}


def generate_slug(db: Session, business_name: str) -> str:
    normalized = unicodedata.normalize("NFKD", business_name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    base_slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_name.lower()).strip("-") or "tenant"
    base_slug = base_slug[:80]
    slug = base_slug
    counter = 1
    while db.query(Tenant.id).filter(Tenant.slug == slug).first() is not None:
        counter += 1
        slug = f"{base_slug[:70]}-{counter}"
    return slug


def get_trial_plan(db: Session) -> SubscriptionPlan:
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.code == "trial",
        SubscriptionPlan.is_active.is_(True),
    ).first()
    if plan is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Trial subscription plan is not configured")
    return plan


def get_tenant_owner_role(db: Session) -> Role:
    role = db.query(Role).filter(Role.name == "Tenant Owner", Role.is_active.is_(True)).first()
    if role is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Tenant Owner role is not configured")
    return role


def validate_registration_uniqueness(db: Session, payload: TenantRegistrationRequest) -> None:
    normalized_email = str(payload.email).strip().lower()
    if db.query(User.id).filter(func.lower(User.email) == normalized_email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")
    if db.query(User.id).filter(func.lower(User.username) == payload.username.lower()).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This username is already in use")


def resolve_enabled_modules(db: Session, plan: SubscriptionPlan, business_type: str) -> list[SystemModule]:
    plan_modules = db.query(SystemModule).join(
        PlanModule, PlanModule.module_id == SystemModule.id
    ).filter(
        PlanModule.plan_id == plan.id,
        PlanModule.is_enabled.is_(True),
        SystemModule.is_active.is_(True),
    ).all()
    allowed_codes = BUSINESS_MODULES.get(business_type)
    if not allowed_codes:
        return plan_modules
    return [module for module in plan_modules if module.is_core or module.code in allowed_codes]


def register_trial_tenant(db: Session, payload: TenantRegistrationRequest) -> dict:
    password_bytes = payload.password.encode("utf-8")
    if len(password_bytes) > 72:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Password is too long. It must not exceed 72 bytes.")

    validate_registration_uniqueness(db, payload)
    trial_plan = get_trial_plan(db)
    owner_role = get_tenant_owner_role(db)
    now = datetime.now(timezone.utc)
    trial_days = trial_plan.trial_days or 14
    trial_ends_at = now + timedelta(days=trial_days)
    email = str(payload.email).strip().lower()
    slug = generate_slug(db, payload.business_name)
    default_locale = "ar-EG" if payload.language == "ar" else "en-US"
    company_name = payload.company_name.strip() if payload.company_name else payload.business_name
    branch_name = payload.branch_name.strip() if payload.branch_name else ("الفرع الرئيسي" if payload.language == "ar" else "Main Branch")

    try:
        tenant = Tenant(
            name=payload.business_name, slug=slug, business_type=payload.business_type,
            owner_name=payload.owner_name, email=email, phone=payload.phone,
            country_code=payload.country_code, default_language=payload.language,
            default_locale=default_locale, timezone="Africa/Cairo", currency_code="EGP",
            status="trial", is_trial=True, trial_started_at=now, trial_ends_at=trial_ends_at, is_active=True,
        )
        db.add(tenant)
        db.flush()

        company = Company(
            tenant_id=tenant.id, name=company_name, code="MAIN", description=None,
            address=None, phone=payload.phone, email=email, tax_id=None, is_active=True,
        )
        db.add(company)
        db.flush()

        branch = Branch(
            tenant_id=tenant.id, company_id=company.id, name=branch_name, code="MAIN",
            address=None, phone=payload.phone, email=email, is_active=True,
        )
        db.add(branch)
        db.flush()

        owner_user = User(
            tenant_id=tenant.id, username=payload.username, email=email,
            full_name=payload.owner_name, phone=payload.phone,
            hashed_password=get_password_hash(str(payload.password)),
            preferred_language=payload.language, is_active=True, is_superuser=False,
            is_platform_admin=False, is_deleted=False, must_change_password=False,
            role_id=owner_role.id,
        )
        db.add(owner_user)
        db.flush()

        subscription = Subscription(
            tenant_id=tenant.id, plan_id=trial_plan.id, status="trialing", billing_cycle="monthly",
            starts_at=now, ends_at=trial_ends_at, trial_ends_at=trial_ends_at,
            next_billing_date=None, is_auto_renew=False,
        )
        db.add(subscription)
        db.flush()

        modules = resolve_enabled_modules(db, trial_plan, payload.business_type)
        for module in modules:
            db.add(TenantModule(
                tenant_id=tenant.id, module_id=module.id, is_enabled=True,
                starts_at=now, ends_at=trial_ends_at,
            ))

        db.commit()
        db.refresh(tenant)
        db.refresh(company)
        db.refresh(branch)
        db.refresh(owner_user)
        db.refresh(subscription)
        return {
            "message": "Trial account created successfully", "tenant": tenant, "company": company,
            "branch": branch, "user": owner_user, "subscription_status": subscription.status,
            "plan_code": trial_plan.code, "enabled_modules": [module.code for module in modules],
            "trial_ends_at": trial_ends_at,
        }
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        logger.exception("Database integrity error while creating trial account")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Registration could not be completed because the account data conflicts with an existing record") from exc
    except Exception as exc:
        db.rollback()
        logger.exception("Unexpected error while creating trial account")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create trial account") from exc
