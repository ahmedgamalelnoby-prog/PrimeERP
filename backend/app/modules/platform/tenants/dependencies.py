from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from .repository import TenantRepository
from .service import TenantService


def get_tenant_repository() -> TenantRepository:
    return TenantRepository()


TenantRepositoryDependency = Annotated[
    TenantRepository,
    Depends(
        get_tenant_repository
    ),
]


def get_tenant_service(
    repository: TenantRepositoryDependency,
) -> TenantService:
    return TenantService(
        repository=repository
    )


TenantServiceDependency = Annotated[
    TenantService,
    Depends(
        get_tenant_service
    ),
]