from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
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


@router.get("/modules")
def list_modules(
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    modules = db.scalars(select(SystemModule).order_by(SystemModule.display_order, SystemModule.id)).all()
    return [
        {
            "id": module.id,
            "code": module.code,
            "name_ar": module.name_ar,
            "name_en": module.name_en,
            "is_core": module.is_core,
            "is_active": module.is_active,
            "display_order": module.display_order,
        }
        for module in modules
    ]


@router.get("/plans/{plan_id}/modules")
def list_plan_modules(
    plan_id: int,
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    if db.get(SubscriptionPlan, plan_id) is None:
        raise HTTPException(status_code=404, detail="Subscription plan not found")
    rows = db.scalars(
        select(SystemModule, PlanModule.is_enabled)
        .outerjoin(PlanModule, (PlanModule.module_id == SystemModule.id) & (PlanModule.plan_id == plan_id))
        .order_by(SystemModule.display_order, SystemModule.id)
    ).all()
    return [
        {"module_id": module.id, "code": module.code, "is_core": module.is_core, "is_enabled": enabled is True}
        for module, enabled in rows
    ]


@router.put("/plans/{plan_id}/modules/{module_id}")
def set_plan_module(
    plan_id: int,
    module_id: int,
    payload: PlanModulePayload,
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    if db.get(SubscriptionPlan, plan_id) is None:
        raise HTTPException(status_code=404, detail="Subscription plan not found")
    module = db.get(SystemModule, module_id)
    if module is None:
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
def list_tenant_modules(
    tenant_id: int,
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    from app.modules.saas.models import Tenant

    if db.get(Tenant, tenant_id) is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    rows = db.scalars(
        select(SystemModule, TenantModule)
        .outerjoin(TenantModule, (TenantModule.module_id == SystemModule.id) & (TenantModule.tenant_id == tenant_id))
        .order_by(SystemModule.display_order, SystemModule.id)
    ).all()
    return [
        {
            "module_id": module.id,
            "code": module.code,
            "is_core": module.is_core,
            "override": None if override is None else {
                "is_enabled": override.is_enabled,
                "starts_at": override.starts_at,
                "ends_at": override.ends_at,
            },
        }
        for module, override in rows
    ]


@router.put("/tenants/{tenant_id}/modules/{module_id}")
def set_tenant_module(
    tenant_id: int,
    module_id: int,
    payload: TenantModulePayload,
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    from app.modules.saas.models import Tenant

    if db.get(Tenant, tenant_id) is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    module = db.get(SystemModule, module_id)
    if module is None:
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
    return {
        "tenant_id": tenant_id,
        "module_id": module_id,
        "is_enabled": row.is_enabled,
        "starts_at": row.starts_at,
        "ends_at": row.ends_at,
    }


@router.patch("/plans/{plan_id}/limits")
def update_plan_limits(
    plan_id: int,
    payload: LimitPayload,
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    plan = db.get(SubscriptionPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Subscription plan not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)
    db.commit()
    db.refresh(plan)
    return {field: getattr(plan, field) for field in payload.model_fields}


@router.get("/plans/{plan_id}/limits")
def get_plan_limits(
    plan_id: int,
    _: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    plan = db.get(SubscriptionPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Subscription plan not found")
    return {
        "plan_id": plan.id,
        "code": plan.code,
        "max_users": plan.max_users,
        "max_companies": plan.max_companies,
        "max_branches": plan.max_branches,
        "max_products": plan.max_products,
        "max_integrations": plan.max_integrations,
        "storage_limit_mb": plan.storage_limit_mb,
    }
