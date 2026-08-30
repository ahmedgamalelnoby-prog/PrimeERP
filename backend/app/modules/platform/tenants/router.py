from __future__ import annotations

from math import ceil
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.database.session import get_db

from .constants import TenantStatus
from .dependencies import TenantServiceDependency
from .schemas import (
    TenantCreate,
    TenantListItem,
    TenantListResponse,
    TenantRead,
    TenantSuspendRequest,
    TenantUpdate,
)


router = APIRouter(
    prefix="/tenants",
    tags=["Platform - Tenants"],
)


DatabaseSession = Annotated[
    Session,
    Depends(
        get_db
    ),
]


@router.get(
    "",
    response_model=TenantListResponse,
    summary="List tenants",
)
def list_tenants(
    db: DatabaseSession,
    service: TenantServiceDependency,
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=200,
    ),
    tenant_status: TenantStatus | None = Query(
        default=None,
        alias="status",
    ),
    is_active: bool | None = Query(
        default=None
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
) -> TenantListResponse:
    items, total = service.list_tenants(
        db,
        search=search,
        tenant_status=(
            tenant_status.value
            if tenant_status is not None
            else None
        ),
        is_active=is_active,
        page=page,
        page_size=page_size,
    )

    pages = (
        ceil(
            total / page_size
        )
        if total > 0
        else 0
    )

    return TenantListResponse(
        items=[
            TenantListItem.model_validate(
                item
            )
            for item in items
        ],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/{tenant_id}",
    response_model=TenantRead,
    summary="Get tenant",
)
def get_tenant(
    tenant_id: int,
    db: DatabaseSession,
    service: TenantServiceDependency,
) -> TenantRead:
    tenant = service.get_tenant_or_raise(
        db,
        tenant_id,
    )

    return TenantRead.model_validate(
        tenant
    )


@router.post(
    "",
    response_model=TenantRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create tenant",
)
def create_tenant(
    payload: TenantCreate,
    db: DatabaseSession,
    service: TenantServiceDependency,
) -> TenantRead:
    try:
        tenant = service.create_tenant(
            db,
            payload,
        )

        db.commit()
        db.refresh(
            tenant
        )

        return TenantRead.model_validate(
            tenant
        )

    except Exception:
        db.rollback()
        raise


@router.put(
    "/{tenant_id}",
    response_model=TenantRead,
    summary="Update tenant",
)
def update_tenant(
    tenant_id: int,
    payload: TenantUpdate,
    db: DatabaseSession,
    service: TenantServiceDependency,
) -> TenantRead:
    try:
        tenant = service.update_tenant(
            db,
            tenant_id,
            payload,
        )

        db.commit()
        db.refresh(
            tenant
        )

        return TenantRead.model_validate(
            tenant
        )

    except Exception:
        db.rollback()
        raise


@router.post(
    "/{tenant_id}/suspend",
    response_model=TenantRead,
    summary="Suspend tenant",
)
def suspend_tenant(
    tenant_id: int,
    payload: TenantSuspendRequest,
    db: DatabaseSession,
    service: TenantServiceDependency,
) -> TenantRead:
    try:
        tenant = service.suspend_tenant(
            db,
            tenant_id,
            reason=payload.reason,
        )

        db.commit()
        db.refresh(
            tenant
        )

        return TenantRead.model_validate(
            tenant
        )

    except Exception:
        db.rollback()
        raise


@router.post(
    "/{tenant_id}/activate",
    response_model=TenantRead,
    summary="Activate tenant",
)
def activate_tenant(
    tenant_id: int,
    db: DatabaseSession,
    service: TenantServiceDependency,
) -> TenantRead:
    try:
        tenant = service.activate_tenant(
            db,
            tenant_id,
        )

        db.commit()
        db.refresh(
            tenant
        )

        return TenantRead.model_validate(
            tenant
        )

    except Exception:
        db.rollback()
        raise


@router.post(
    "/{tenant_id}/resume",
    response_model=TenantRead,
    summary="Resume suspended tenant",
)
def resume_tenant(
    tenant_id: int,
    db: DatabaseSession,
    service: TenantServiceDependency,
) -> TenantRead:
    try:
        tenant = service.resume_tenant(
            db,
            tenant_id,
        )

        db.commit()
        db.refresh(
            tenant
        )

        return TenantRead.model_validate(
            tenant
        )

    except Exception:
        db.rollback()
        raise


@router.post(
    "/{tenant_id}/cancel",
    response_model=TenantRead,
    summary="Cancel tenant",
)
def cancel_tenant(
    tenant_id: int,
    db: DatabaseSession,
    service: TenantServiceDependency,
) -> TenantRead:
    try:
        tenant = service.cancel_tenant(
            db,
            tenant_id,
        )

        db.commit()
        db.refresh(
            tenant
        )

        return TenantRead.model_validate(
            tenant
        )

    except Exception:
        db.rollback()
        raise


@router.post(
    "/{tenant_id}/expire-trial",
    response_model=TenantRead,
    summary="Expire tenant trial",
)
def expire_tenant_trial(
    tenant_id: int,
    db: DatabaseSession,
    service: TenantServiceDependency,
) -> TenantRead:
    try:
        tenant = service.expire_trial(
            db,
            tenant_id,
        )

        db.commit()
        db.refresh(
            tenant
        )

        return TenantRead.model_validate(
            tenant
        )

    except Exception:
        db.rollback()
        raise


@router.delete(
    "/{tenant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tenant permanently",
)
def delete_tenant(
    tenant_id: int,
    db: DatabaseSession,
    service: TenantServiceDependency,
) -> Response:
    try:
        tenant = service.get_tenant_or_raise(
            db,
            tenant_id,
            for_update=True,
        )

        service.delete(
            db,
            tenant,
        )

        db.commit()

        return Response(
            status_code=status.HTTP_204_NO_CONTENT
        )

    except Exception:
        db.rollback()
        raise