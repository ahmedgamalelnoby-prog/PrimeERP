from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.services.base_crud_service import BaseCRUDService
from app.modules.saas.models import Subscription, Tenant

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
    def __init__(self, repository: TenantRepository | None = None) -> None:
        super().__init__(repository or TenantRepository())

    def get_tenant_or_raise(self, db: Session, tenant_id: int, *, for_update: bool = False) -> Tenant:
        tenant = self.repository.get_by_id(db, tenant_id, for_update=for_update)
        if tenant is None:
            raise TenantNotFoundError(tenant_id)
        return tenant

    def get_by_slug_or_raise(self, db: Session, slug: str) -> Tenant:
        tenant = self.repository.get_by_slug(db, slug)
        if tenant is None:
            raise TenantNotFoundError(slug)
        return tenant

    @staticmethod
    def _subscription_is_current(subscription: Subscription | None) -> bool:
        if subscription is None or subscription.status not in {"trialing", "active", "past_due"}:
            return False
        now = datetime.now(timezone.utc)
        starts_at = subscription.starts_at
        ends_at = subscription.ends_at
        if starts_at is not None:
            if starts_at.tzinfo is None:
                starts_at = starts_at.replace(tzinfo=timezone.utc)
            if starts_at > now:
                return False
        if ends_at is not None:
            if ends_at.tzinfo is None:
                ends_at = ends_at.replace(tzinfo=timezone.utc)
            if ends_at <= now:
                return False
        if subscription.status == "trialing" and subscription.trial_ends_at is not None:
            trial_end = subscription.trial_ends_at
            if trial_end.tzinfo is None:
                trial_end = trial_end.replace(tzinfo=timezone.utc)
            if trial_end <= now:
                return False
        return True

    def _current_subscription(self, db: Session, tenant_id: int, *, for_update: bool = False) -> Subscription | None:
        now = datetime.now(timezone.utc)
        query = (
            db.query(Subscription)
            .filter(
                Subscription.tenant_id == tenant_id,
                Subscription.status.in_(("trialing", "active", "past_due")),
                Subscription.starts_at <= now,
                or_(Subscription.ends_at.is_(None), Subscription.ends_at > now),
            )
            .order_by(Subscription.ends_at.desc().nullslast(), Subscription.id.desc())
        )
        if for_update:
            query = query.with_for_update()
        subscription = query.first()
        return subscription if self._subscription_is_current(subscription) else None

    def _require_current_subscription(self, db: Session, tenant_id: int) -> Subscription:
        subscription = self._current_subscription(db, tenant_id, for_update=True)
        if subscription is None:
            raise InvalidTenantStatusTransitionError("no_active_subscription", TenantStatus.ACTIVE.value)
        return subscription

    def create_tenant(self, db: Session, data: TenantCreate) -> Tenant:
        payload = data.model_dump()
        slug = payload["slug"]
        if self.repository.slug_exists(db, slug):
            raise TenantSlugAlreadyExistsError(slug)
        now = utc_now()
        if payload.get("is_trial", True):
            payload["status"] = TenantStatus.TRIAL.value
            payload["is_active"] = True
            if payload.get("trial_started_at") is None:
                payload["trial_started_at"] = now
            if payload.get("trial_ends_at") is None:
                payload["trial_ends_at"] = payload["trial_started_at"] + timedelta(days=DEFAULT_TRIAL_DAYS)
        else:
            payload["status"] = TenantStatus.ACTIVE.value
            payload["is_active"] = True
            payload["trial_started_at"] = None
            payload["trial_ends_at"] = None
        return self.repository.create(db, data=payload)

    def update_tenant(self, db: Session, tenant_id: int, data: TenantUpdate) -> Tenant:
        tenant = self.get_tenant_or_raise(db, tenant_id, for_update=True)
        payload = data.model_dump(exclude_unset=True)
        new_slug = payload.get("slug")
        if new_slug is not None and self.repository.slug_exists(db, new_slug, exclude_id=tenant.id):
            raise TenantSlugAlreadyExistsError(new_slug)
        return self.repository.update(db, tenant, data=payload)

    def suspend_tenant(self, db: Session, tenant_id: int, *, reason: str) -> Tenant:
        tenant = self.get_tenant_or_raise(db, tenant_id, for_update=True)
        if tenant.status == TenantStatus.SUSPENDED.value:
            raise TenantAlreadySuspendedError(tenant.id)
        if tenant.status == TenantStatus.CANCELLED.value:
            raise InvalidTenantStatusTransitionError(tenant.status, TenantStatus.SUSPENDED.value)
        cleaned_reason = reason.strip()
        if not cleaned_reason:
            raise ValueError("Suspension reason is required")
        tenant.status = TenantStatus.SUSPENDED.value
        tenant.is_active = False
        tenant.suspended_at = utc_now()
        tenant.suspension_reason = cleaned_reason
        db.add(tenant)
        db.flush()
        return tenant

    def activate_tenant(self, db: Session, tenant_id: int) -> Tenant:
        tenant = self.get_tenant_or_raise(db, tenant_id, for_update=True)
        if tenant.status == TenantStatus.CANCELLED.value:
            raise InvalidTenantStatusTransitionError(tenant.status, TenantStatus.ACTIVE.value)
        if tenant.status == TenantStatus.EXPIRED.value:
            raise InvalidTenantStatusTransitionError(tenant.status, TenantStatus.ACTIVE.value)
        self._require_current_subscription(db, tenant.id)
        tenant.status = TenantStatus.ACTIVE.value
        tenant.is_active = True
        tenant.is_trial = False
        tenant.suspended_at = None
        tenant.suspension_reason = None
        db.add(tenant)
        db.flush()
        return tenant

    def resume_tenant(self, db: Session, tenant_id: int) -> Tenant:
        tenant = self.get_tenant_or_raise(db, tenant_id, for_update=True)
        if tenant.status != TenantStatus.SUSPENDED.value:
            raise TenantNotSuspendedError(tenant.id)
        self._require_current_subscription(db, tenant.id)
        tenant.status = TenantStatus.ACTIVE.value
        tenant.is_active = True
        tenant.suspended_at = None
        tenant.suspension_reason = None
        db.add(tenant)
        db.flush()
        return tenant

    def cancel_tenant(self, db: Session, tenant_id: int) -> Tenant:
        tenant = self.get_tenant_or_raise(db, tenant_id, for_update=True)
        if tenant.status == TenantStatus.CANCELLED.value:
            return tenant
        now = utc_now()
        subscriptions = (
            db.query(Subscription)
            .filter(
                Subscription.tenant_id == tenant.id,
                Subscription.status.in_(("trialing", "active", "past_due")),
            )
            .with_for_update()
            .all()
        )
        for subscription in subscriptions:
            subscription.status = "cancelled"
            subscription.cancelled_at = now
            subscription.is_auto_renew = False
            subscription.next_billing_date = None
        tenant.status = TenantStatus.CANCELLED.value
        tenant.is_active = False
        tenant.is_trial = False
        tenant.suspended_at = None
        tenant.suspension_reason = None
        db.add(tenant)
        db.flush()
        return tenant

    def expire_trial(self, db: Session, tenant_id: int) -> Tenant:
        tenant = self.get_tenant_or_raise(db, tenant_id, for_update=True)
        if not tenant.is_trial:
            raise InvalidTenantStatusTransitionError(tenant.status, TenantStatus.EXPIRED.value)
        subscription = self._current_subscription(db, tenant.id, for_update=True)
        if subscription is not None and subscription.status == "trialing":
            subscription.status = "expired"
            subscription.is_auto_renew = False
            subscription.next_billing_date = None
            subscription.cancelled_at = utc_now()
        tenant.status = TenantStatus.EXPIRED.value
        tenant.is_active = False
        tenant.is_trial = False
        db.add(tenant)
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
        offset = (page - 1) * page_size
        return self.repository.list_tenants(
            db,
            search=search,
            status=tenant_status,
            is_active=is_active,
            offset=offset,
            limit=page_size,
        )
