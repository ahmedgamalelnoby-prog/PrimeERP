from __future__ import annotations

from math import ceil
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .constants import TenantStatus
from .dependencies import TenantServiceDependency
from .schemas import TenantCreate, TenantListItem, TenantListResponse, TenantRead, TenantSuspendRequest, TenantUpdate


router = APIRouter(prefix="/tenants", tags=["Platform - Tenants"])

DatabaseSession = Annotated[Session, Depends(get_db)]


def require_platform_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform administrator access required")
    return current_user


@router.get("", response_model=TenantListResponse, summary="List tenants", dependencies=[Depends(require_platform_admin)])
def list_tenants(
    db: DatabaseSession,
    service: TenantServiceDependency,
    search: str | None = Query(default=None, min_length=1, max_length=200),
    tenant_status: TenantStatus | None = Query(default=None, alias="status"),
    is_active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> TenantListResponse:
    items, total = service.list_tenants(
        db,
        search=search,
        tenant_status=tenant_status.value if tenant_status is not None else None,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )
    pages = ceil(total / page_size) if total > 0 else 0
    return TenantListResponse(
        items=[TenantListItem.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{tenant_id}", response_model=TenantRead, summary="Get tenant", dependencies=[Depends(require_platform_admin)])
def get_tenant(tenant_id: int, db: DatabaseSession, service: TenantServiceDependency) -> TenantRead:
    tenant = service.get_tenant_or_raise(db, tenant_id)
    return TenantRead.model_validate(tenant)


@router.post("", response_model=TenantRead, status_code=status.HTTP_201_CREATED, summary="Create tenant", dependencies=[Depends(require_platform_admin)])
def create_tenant(payload: TenantCreate, db: DatabaseSession, service: TenantServiceDependency) -> TenantRead:
    try:
        tenant = service.create_tenant(db, payload)
        db.commit()
        db.refresh(tenant)
        return TenantRead.model_validate(tenant)
    except Exception:
        db.rollback()
        raise


@router.put("/{tenant_id}", response_model=TenantRead, summary="Update tenant", dependencies=[Depends(require_platform_admin)])
def update_tenant(tenant_id: int, payload: TenantUpdate, db: DatabaseSession, service: TenantServiceDependency) -> TenantRead:
    try:
        tenant = service.update_tenant(db, tenant_id, payload)
        db.commit()
        db.refresh(tenant)
        return TenantRead.model_validate(tenant)
    except Exception:
        db.rollback()
        raise


@router.post("/{tenant_id}/suspend", response_model=TenantRead, summary="Suspend tenant", dependencies=[Depends(require_platform_admin)])
def suspend_tenant(tenant_id: int, payload: TenantSuspendRequest, db: DatabaseSession, service: TenantServiceDependency) -> TenantRead:
    try:
        tenant = service.suspend_tenant(db, tenant_id, reason=payload.reason)
        db.commit()
        db.refresh(tenant)
        return TenantRead.model_validate(tenant)
    except Exception:
        db.rollback()
        raise


@router.post("/{tenant_id}/activate", response_model=TenantRead, summary="Activate tenant", dependencies=[Depends(require_platform_admin)])
def activate_tenant(tenant_id: int, db: DatabaseSession, service: TenantServiceDependency) -> TenantRead:
    try:
        tenant = service.activate_tenant(db, tenant_id)
        db.commit()
        db.refresh(tenant)
        return TenantRead.model_validate(tenant)
    except Exception:
        db.rollback()
        raise


@router.post("/{tenant_id}/resume", response_model=TenantRead, summary="Resume suspended tenant", dependencies=[Depends(require_platform_admin)])
def resume_tenant(tenant_id: int, db: DatabaseSession, service: TenantServiceDependency) -> TenantRead:
    try:
        tenant = service.resume_tenant(db, tenant_id)
        db.commit()
        db.refresh(tenant)
        return TenantRead.model_validate(tenant)
    except Exception:
        db.rollback()
        raise


@router.post("/{tenant_id}/cancel", response_model=TenantRead, summary="Cancel tenant", dependencies=[Depends(require_platform_admin)])
def cancel_tenant(tenant_id: int, db: DatabaseSession, service: TenantServiceDependency) -> TenantRead:
    try:
        tenant = service.cancel_tenant(db, tenant_id)
        db.commit()
        db.refresh(tenant)
        return TenantRead.model_validate(tenant)
    except Exception:
        db.rollback()
        raise


@router.post("/{tenant_id}/expire-trial", response_model=TenantRead, summary="Expire tenant trial", dependencies=[Depends(require_platform_admin)])
def expire_tenant_trial(tenant_id: int, db: DatabaseSession, service: TenantServiceDependency) -> TenantRead:
    try:
        tenant = service.expire_trial(db, tenant_id)
        db.commit()
        db.refresh(tenant)
        return TenantRead.model_validate(tenant)
    except Exception:
        db.rollback()
        raise


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete tenant permanently", dependencies=[Depends(require_platform_admin)])
def delete_tenant(tenant_id: int, db: DatabaseSession, service: TenantServiceDependency) -> Response:
    try:
        tenant = service.get_tenant_or_raise(db, tenant_id, for_update=True)
        service.delete(db, tenant)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception:
        db.rollback()
        raise
