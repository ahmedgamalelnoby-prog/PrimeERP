from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.services.base_crud_service import BaseCRUDService
from app.modules.saas.models import Tenant

from .constants import (
    DEFAULT_TRIAL_DAYS,
    TenantStatus,
)
from .exceptions import (
    InvalidTenantStatusTransitionError,
    TenantAlreadySuspendedError,
    TenantNotFoundError,
    TenantNotSuspendedError,
    TenantSlugAlreadyExistsError,
)
from .repository import TenantRepository
from .schemas import (
    TenantCreate,
    TenantUpdate,
)
from .validators import utc_now


class TenantService(
    BaseCRUDService[Tenant, TenantRepository]
):
    def __init__(
        self,
        repository: TenantRepository | None = None,
    ) -> None:
        super().__init__(
            repository or TenantRepository()
        )

    def get_tenant_or_raise(
        self,
        db: Session,
        tenant_id: int,
        *,
        for_update: bool = False,
    ) -> Tenant:
        tenant = self.repository.get_by_id(
            db,
            tenant_id,
            for_update=for_update,
        )

        if tenant is None:
            raise TenantNotFoundError(
                tenant_id
            )

        return tenant

    def get_by_slug_or_raise(
        self,
        db: Session,
        slug: str,
    ) -> Tenant:
        tenant = self.repository.get_by_slug(
            db,
            slug,
        )

        if tenant is None:
            raise TenantNotFoundError(
                slug
            )

        return tenant

    def create_tenant(
        self,
        db: Session,
        data: TenantCreate,
    ) -> Tenant:
        payload = data.model_dump()

        slug = payload["slug"]

        if self.repository.slug_exists(
            db,
            slug,
        ):
            raise TenantSlugAlreadyExistsError(
                slug
            )

        now = utc_now()

        if payload.get("is_trial", True):
            payload["status"] = TenantStatus.TRIAL.value
            payload["is_active"] = True

            if payload.get("trial_started_at") is None:
                payload["trial_started_at"] = now

            if payload.get("trial_ends_at") is None:
                payload["trial_ends_at"] = (
                    payload["trial_started_at"]
                    + timedelta(
                        days=DEFAULT_TRIAL_DAYS
                    )
                )
        else:
            payload["status"] = TenantStatus.ACTIVE.value
            payload["is_active"] = True
            payload["trial_started_at"] = None
            payload["trial_ends_at"] = None

        tenant = self.repository.create(
            db,
            data=payload,
        )

        return tenant

    def update_tenant(
        self,
        db: Session,
        tenant_id: int,
        data: TenantUpdate,
    ) -> Tenant:
        tenant = self.get_tenant_or_raise(
            db,
            tenant_id,
            for_update=True,
        )

        payload = data.model_dump(
            exclude_unset=True
        )

        new_slug = payload.get(
            "slug"
        )

        if (
            new_slug is not None
            and self.repository.slug_exists(
                db,
                new_slug,
                exclude_id=tenant.id,
            )
        ):
            raise TenantSlugAlreadyExistsError(
                new_slug
            )

        return self.repository.update(
            db,
            tenant,
            data=payload,
        )

    def suspend_tenant(
        self,
        db: Session,
        tenant_id: int,
        *,
        reason: str,
    ) -> Tenant:
        tenant = self.get_tenant_or_raise(
            db,
            tenant_id,
            for_update=True,
        )

        if tenant.status == TenantStatus.SUSPENDED.value:
            raise TenantAlreadySuspendedError(
                tenant.id
            )

        if tenant.status == TenantStatus.CANCELLED.value:
            raise InvalidTenantStatusTransitionError(
                tenant.status,
                TenantStatus.SUSPENDED.value,
            )

        tenant.status = TenantStatus.SUSPENDED.value
        tenant.is_active = False
        tenant.suspended_at = utc_now()
        tenant.suspension_reason = reason.strip()

        db.add(
            tenant
        )
        db.flush()

        return tenant

    def activate_tenant(
        self,
        db: Session,
        tenant_id: int,
    ) -> Tenant:
        tenant = self.get_tenant_or_raise(
            db,
            tenant_id,
            for_update=True,
        )

        if tenant.status == TenantStatus.CANCELLED.value:
            raise InvalidTenantStatusTransitionError(
                tenant.status,
                TenantStatus.ACTIVE.value,
            )

        if tenant.status == TenantStatus.EXPIRED.value:
            raise InvalidTenantStatusTransitionError(
                tenant.status,
                TenantStatus.ACTIVE.value,
            )

        tenant.status = TenantStatus.ACTIVE.value
        tenant.is_active = True
        tenant.is_trial = False
        tenant.suspended_at = None
        tenant.suspension_reason = None

        db.add(
            tenant
        )
        db.flush()

        return tenant

    def resume_tenant(
        self,
        db: Session,
        tenant_id: int,
    ) -> Tenant:
        tenant = self.get_tenant_or_raise(
            db,
            tenant_id,
            for_update=True,
        )

        if tenant.status != TenantStatus.SUSPENDED.value:
            raise TenantNotSuspendedError(
                tenant.id
            )

        tenant.status = TenantStatus.ACTIVE.value
        tenant.is_active = True
        tenant.suspended_at = None
        tenant.suspension_reason = None

        db.add(
            tenant
        )
        db.flush()

        return tenant

    def cancel_tenant(
        self,
        db: Session,
        tenant_id: int,
    ) -> Tenant:
        tenant = self.get_tenant_or_raise(
            db,
            tenant_id,
            for_update=True,
        )

        if tenant.status == TenantStatus.CANCELLED.value:
            return tenant

        tenant.status = TenantStatus.CANCELLED.value
        tenant.is_active = False
        tenant.is_trial = False
        tenant.suspended_at = None
        tenant.suspension_reason = None

        db.add(
            tenant
        )
        db.flush()

        return tenant

    def expire_trial(
        self,
        db: Session,
        tenant_id: int,
    ) -> Tenant:
        tenant = self.get_tenant_or_raise(
            db,
            tenant_id,
            for_update=True,
        )

        if not tenant.is_trial:
            raise InvalidTenantStatusTransitionError(
                tenant.status,
                TenantStatus.EXPIRED.value,
            )

        tenant.status = TenantStatus.EXPIRED.value
        tenant.is_active = False
        tenant.is_trial = False

        db.add(
            tenant
        )
        db.flush()

        return tenant

    def list_tenants(
        self,
        db: Session,
        *,
        search: str | None = None,
        tenant_status: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Tenant], int]:
        offset = (
            page - 1
        ) * page_size

        return self.repository.list_tenants(
            db,
            search=search,
            status=tenant_status,
            is_active=is_active,
            offset=offset,
            limit=page_size,
        )