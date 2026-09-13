from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.platform.plans.models import Plan
from app.modules.saas.models import PlanModule, SubscriptionPlan, SystemModule, TenantModule

router = APIRouter(prefix="/platform/entitlements", tags=["Platform Entitlements"])


def require_platform_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_platform_admin and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform administrator access is required")
    return current_user


class PlanModulePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_enabled: bool = True


class TenantModulePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_enabled: bool = True
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class LimitPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    max_users: int | None = Field(default=None, ge=1)
    max_companies: int | None = Field(default=None, ge=1)
    max_branches: int | None = Field(default=None, ge=1)
    max_products: int | None = Field(default=None, ge=1)
    max_integrations: int | None = Field(default=None, ge=0)
    storage_limit_mb: int | None = Field(default=None, ge=1)


LIMIT_FIELDS = ("max_users", "max_companies", "max_branches", "max_products", "max_integrations", "storage_limit_mb")


@router.get("/modules")
def list_modules(_: User = Depends(require_platform_admin), db: Session = Depends(get_db)):
    modules = db.scalars(select(SystemModule).order_by(SystemModule.display_order, SystemModule.id)).all()
    return [{"id": m.id, "code": m.code, "name_ar": m.name_ar, "name_en": m.name_en, "is_core": m.is_core, "is_active": m.is_active, "display_order": m.display_order} for m in modules]


@router.get("/plans/{plan_id}/modules")
def list_plan_modules(plan_id: int, _: User = Depends(require_platform_admin), db: Session = Depends(get_db)):
    if db.get(SubscriptionPlan, plan_id) is None:
        raise HTTPException(status_code=404, detail="Subscription plan not found")
    rows = db.execute(
        select(SystemModule, PlanModule.is_enabled)
        .outerjoin(PlanModule, (PlanModule.module_id == SystemModule.id) & (PlanModule.plan_id == plan_id))
        .order_by(SystemModule.display_order, SystemModule.id)
    ).all()
    return [{"module_id": m.id, "code": m.code, "is_core": m.is_core, "is_enabled": enabled is True} for m, enabled in rows]


@router.put("/plans/{plan_id}/modules/{module_id}")
def set_plan_module(plan_id: int, module_id: int, payload: PlanModulePayload, _: User = Depends(require_platform_admin), db: Session = Depends(get_db)):
    if db.get(SubscriptionPlan, plan_id) is None:
        raise HTTPException(status_code=404, detail="Subscription plan not found")
    if db.get(SystemModule, module_id) is None:
        raise HTTPException(status_code=404, detail="System module not found")
    row = db.scalar(select(PlanModule).where(PlanModule.plan_id == plan_id, PlanModule.module_id == module_id))
    if row is None:
        row = PlanModule(plan_id=plan_id, module_id=module_id, is_enabled=payload.is_enabled)
        db.add(row)
    else:
        row.is_enabled = payload.is_enabled
    db.commit()
    db.refresh(row)
    return {"plan_id": plan_id, "module_id": module_id, "is_enabled": row.is_enabled}


@router.get("/tenants/{tenant_id}/modules")
def list_tenant_modules(tenant_id: int, _: User = Depends(require_platform_admin), db: Session = Depends(get_db)):
    from app.modules.saas.models import Tenant
    if db.get(Tenant, tenant_id) is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    rows = db.execute(
        select(SystemModule, TenantModule)
        .outerjoin(TenantModule, (TenantModule.module_id == SystemModule.id) & (TenantModule.tenant_id == tenant_id))
        .order_by(SystemModule.display_order, SystemModule.id)
    ).all()
    return [{"module_id": m.id, "code": m.code, "is_core": m.is_core,
             "override": None if override is None else {"is_enabled": override.is_enabled, "starts_at": override.starts_at, "ends_at": override.ends_at}}
            for m, override in rows]


@router.put("/tenants/{tenant_id}/modules/{module_id}")
def set_tenant_module(tenant_id: int, module_id: int, payload: TenantModulePayload, _: User = Depends(require_platform_admin), db: Session = Depends(get_db)):
    from app.modules.saas.models import Tenant
    if db.get(Tenant, tenant_id) is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if db.get(SystemModule, module_id) is None:
        raise HTTPException(status_code=404, detail="System module not found")
    if payload.ends_at is not None and payload.starts_at is not None and payload.ends_at <= payload.starts_at:
        raise HTTPException(status_code=422, detail="ends_at must be later than starts_at")
    row = db.scalar(select(TenantModule).where(TenantModule.tenant_id == tenant_id, TenantModule.module_id == module_id))
    if row is None:
        row = TenantModule(tenant_id=tenant_id, module_id=module_id)
        db.add(row)
    row.is_enabled = payload.is_enabled
    row.starts_at = payload.starts_at
    row.ends_at = payload.ends_at
    db.commit()
    db.refresh(row)
    return {"tenant_id": tenant_id, "module_id": module_id, "is_enabled": row.is_enabled, "starts_at": row.starts_at, "ends_at": row.ends_at}


@router.patch("/plans/{plan_id}/limits")
def update_plan_limits(plan_id: int, payload: LimitPayload, _: User = Depends(require_platform_admin), db: Session = Depends(get_db)):
    canonical = db.get(Plan, plan_id)
    legacy = db.get(SubscriptionPlan, plan_id)
    if canonical is None and legacy is None:
        raise HTTPException(status_code=404, detail="Subscription plan not found")
    values = payload.model_dump(exclude_unset=True)
    for field, value in values.items():
        if canonical is not None:
            setattr(canonical, field, value)
        if legacy is not None:
            setattr(legacy, field, value)
    db.commit()
    source = canonical or legacy
    return {"plan_id": plan_id, **{field: getattr(source, field) for field in LIMIT_FIELDS}}


@router.get("/plans/{plan_id}/limits")
def get_plan_limits(plan_id: int, _: User = Depends(require_platform_admin), db: Session = Depends(get_db)):
    canonical = db.get(Plan, plan_id)
    legacy = db.get(SubscriptionPlan, plan_id)
    if canonical is None and legacy is None:
        raise HTTPException(status_code=404, detail="Subscription plan not found")
    source = canonical or legacy
    return {"plan_id": plan_id, "code": source.code, **{field: getattr(source, field) for field in LIMIT_FIELDS}}
