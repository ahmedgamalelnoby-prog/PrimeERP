from datetime import (
    datetime,
    timezone,
)

from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.modules.identity.repositories.user_repository import (
    user_repository,
)
from app.modules.identity.schemas.auth import (
    LoginRequest,
)
from app.modules.identity.services.password_service import (
    password_service,
)
from app.modules.identity.services.token_service import (
    token_service,
)
from app.modules.saas.models import (
    PlanModule,
    Subscription,
    SubscriptionPlan,
    SystemModule,
    Tenant,
    TenantModule,
)


class AuthenticationService:
    def login(
        self,
        db: Session,
        payload: LoginRequest,
    ) -> dict:
        users = user_repository.find_for_login(
            db=db,
            login=payload.login,
            tenant_slug=payload.tenant_slug,
        )

        if not users:
            self._raise_invalid_credentials()

        if len(users) > 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Multiple accounts match this login. "
                    "Please provide tenant_slug."
                ),
            )

        user = users[0]

        if not password_service.verify_password(
            payload.password,
            user.hashed_password,
        ):
            self._raise_invalid_credentials()

        self._validate_user(user)

        tenant = None
        subscription = None
        enabled_modules: list[str] = []

        if not user.is_platform_admin:
            tenant = self._get_valid_tenant(
                db=db,
                tenant_id=user.tenant_id,
            )

            subscription = self._get_valid_subscription(
                db=db,
                tenant_id=tenant.id,
            )

            enabled_modules = self._get_enabled_modules(
                db=db,
                tenant_id=tenant.id,
                plan_id=subscription.plan_id,
            )

        user.last_login = datetime.now(timezone.utc)

        access_token, expires_in = (
            token_service.create_access_token(user)
        )

        refresh_token = (
            token_service.create_refresh_token(user)
        )

        db.commit()
        db.refresh(user)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "user": {
                "id": user.id,
                "tenant_id": user.tenant_id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role_id": user.role_id,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "is_platform_admin": user.is_platform_admin,
                "preferred_language": user.preferred_language,
                "tenant_slug": (
                    tenant.slug
                    if tenant
                    else None
                ),
                "tenant_name": (
                    tenant.name
                    if tenant
                    else None
                ),
                "tenant_status": (
                    tenant.status
                    if tenant
                    else None
                ),
                "subscription_status": (
                    subscription.status
                    if subscription
                    else None
                ),
                "enabled_modules": enabled_modules,
            },
        }

    def refresh(
        self,
        db: Session,
        refresh_token: str,
    ) -> dict:
        payload = token_service.decode_token(
            refresh_token,
            expected_type="refresh",
        )

        if payload is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_401_UNAUTHORIZED
                ),
                detail="Invalid refresh token",
            )

        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(
                status_code=(
                    status.HTTP_401_UNAUTHORIZED
                ),
                detail="Invalid refresh token",
            )

        user = user_repository.get_by_id(
            db=db,
            user_id=int(user_id),
        )

        if user is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_401_UNAUTHORIZED
                ),
                detail="User not found",
            )

        self._validate_user(user)

        if not user.is_platform_admin:
            self._get_valid_tenant(
                db=db,
                tenant_id=user.tenant_id,
            )

            self._get_valid_subscription(
                db=db,
                tenant_id=user.tenant_id,
            )

        access_token, expires_in = (
            token_service
            .create_access_token(user)
        )

        new_refresh_token = (
            token_service
            .create_refresh_token(user)
        )

        return {
            "access_token": access_token,
            "refresh_token": (
                new_refresh_token
            ),
            "token_type": "bearer",
            "expires_in": expires_in,
        }

    @staticmethod
    def _validate_user(user) -> None:
        if user.is_deleted:
            raise HTTPException(
                status_code=(
                    status.HTTP_401_UNAUTHORIZED
                ),
                detail=(
                    "User account has been deleted"
                ),
            )

        if not user.is_active:
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "User account is inactive"
                ),
            )

    @staticmethod
    def _get_valid_tenant(
        db: Session,
        tenant_id: int | None,
    ) -> Tenant:
        if tenant_id is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "User is not assigned to a tenant"
                ),
            )

        tenant = (
            db.query(Tenant)
            .filter(
                Tenant.id == tenant_id,
            )
            .first()
        )

        if tenant is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail="Tenant not found",
            )

        if not tenant.is_active:
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail="Tenant is inactive",
            )

        if tenant.status in {
            "suspended",
            "cancelled",
            "expired",
        }:
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    f"Tenant status is "
                    f"{tenant.status}"
                ),
            )

        return tenant

    @staticmethod
    def _get_valid_subscription(
        db: Session,
        tenant_id: int,
    ) -> Subscription:
        now = datetime.now(timezone.utc)
        subscription = (
            db.query(Subscription)
            .filter(
                Subscription.tenant_id == tenant_id,
                Subscription.status.in_(
                    ["trialing", "active", "past_due"]
                ),
                or_(
                    Subscription.ends_at.is_(None),
                    Subscription.ends_at > now,
                ),
            )
            .order_by(
                Subscription.ends_at.desc().nullslast(),
                Subscription.id.desc(),
            )
            .first()
        )

        if subscription is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "No active subscription"
                ),
            )

        return subscription

    @staticmethod
    def _get_enabled_modules(
        db: Session,
        tenant_id: int,
        plan_id: int,
    ) -> list[str]:
        active_modules = (
            db.query(SystemModule)
            .filter(SystemModule.is_active.is_(True))
            .all()
        )
        plan_enabled = {
            row.module_id
            for row in db.query(PlanModule.module_id)
            .filter(
                PlanModule.plan_id == plan_id,
                PlanModule.is_enabled.is_(True),
            )
            .all()
        }
        overrides = {
            row.module_id: row
            for row in db.query(TenantModule)
            .filter(TenantModule.tenant_id == tenant_id)
            .all()
        }
        now = datetime.now(timezone.utc)
        enabled: list[SystemModule] = []

        for module in active_modules:
            override = overrides.get(module.id)
            if override is not None:
                if not override.is_enabled:
                    continue
                if override.starts_at is not None and override.starts_at > now:
                    continue
                if override.ends_at is not None and override.ends_at <= now:
                    continue
                enabled.append(module)
            elif module.id in plan_enabled:
                enabled.append(module)

        return [
            module.code
            for module in sorted(
                enabled,
                key=lambda item: (item.display_order, item.id),
            )
        ]

    @staticmethod
    def _raise_invalid_credentials() -> None:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Incorrect login or password"
            ),
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )


authentication_service = (
    AuthenticationService()
)
