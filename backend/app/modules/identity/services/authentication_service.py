from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.audit.service import record_audit_event
from app.modules.identity.models.refresh_token import RefreshToken
from app.modules.identity.repositories.user_repository import user_repository
from app.modules.identity.schemas.auth import LoginRequest
from app.modules.identity.services.password_service import password_service
from app.modules.identity.services.refresh_token_service import RefreshTokenReuseError, refresh_token_service
from app.modules.identity.services.token_service import token_service
from app.modules.saas.models import Subscription, SystemModule, Tenant, TenantModule


class AuthenticationService:
    def login(self, db: Session, payload: LoginRequest) -> dict:
        users = user_repository.find_for_login(db=db, login=payload.login, tenant_slug=payload.tenant_slug)
        if not users:
            self._raise_invalid_credentials()
        if len(users) > 1:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Multiple accounts match this login. Please provide tenant_slug.")
        user = users[0]
        if not password_service.verify_password(payload.password, user.hashed_password):
            self._raise_invalid_credentials()
        self._validate_user(user)

        tenant = None
        subscription = None
        enabled_modules: list[str] = []
        if not user.is_platform_admin:
            tenant = self._get_auth_tenant(db, user.tenant_id)
            subscription = self._get_latest_subscription(db, tenant.id)
            if subscription is not None and self._subscription_is_expired(subscription):
                subscription.status = "expired"
                tenant.status = "expired"
                tenant.is_active = False
            enabled_modules = self._get_enabled_modules(db, tenant.id)

        user.last_login = datetime.now(timezone.utc)
        access_token, expires_in = token_service.create_access_token(user)
        refresh_token = refresh_token_service.issue(db, user.id)
        record_audit_event(
            db,
            action="login.success",
            entity_type="user",
            entity_id=user.id,
            user_id=user.id,
            tenant_id=user.tenant_id,
            metadata={"login": payload.login},
        )
        db.commit()
        db.refresh(user)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "user": {
                "id": user.id, "tenant_id": user.tenant_id, "username": user.username,
                "email": user.email, "full_name": user.full_name, "role_id": user.role_id,
                "is_active": user.is_active, "is_superuser": user.is_superuser,
                "is_platform_admin": user.is_platform_admin, "preferred_language": user.preferred_language,
                "tenant_slug": tenant.slug if tenant else None,
                "tenant_name": tenant.name if tenant else None,
                "tenant_status": tenant.status if tenant else None,
                "subscription_status": subscription.status if subscription else None,
                "enabled_modules": enabled_modules,
            },
        }

    def refresh(self, db: Session, refresh_token: str) -> dict:
        try:
            record = refresh_token_service.consume(db, refresh_token)
        except RefreshTokenReuseError as exc:
            db.commit()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token reuse detected; the session family has been revoked") from exc
        if record is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
        user = user_repository.get_by_id(db=db, user_id=record.user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        self._validate_user(user)
        tenant = None
        if not user.is_platform_admin:
            tenant = self._get_auth_tenant(db, user.tenant_id)
            subscription = self._get_latest_subscription(db, tenant.id)
            if subscription is not None and self._subscription_is_expired(subscription):
                subscription.status = "expired"
                tenant.status = "expired"
                tenant.is_active = False

        access_token, expires_in = token_service.create_access_token(user)
        new_refresh_token = refresh_token_service.issue(db, user.id, family_id=record.family_id)
        db.flush()
        new_record = db.query(RefreshToken).filter(
            RefreshToken.token_hash == refresh_token_service.hash_token(new_refresh_token)
        ).first()
        if new_record is not None:
            record.replaced_by_id = new_record.id
        record_audit_event(
            db,
            action="token.refresh",
            entity_type="user",
            entity_id=user.id,
            user_id=user.id,
            tenant_id=user.tenant_id,
            metadata={"refresh_family_id": record.family_id},
        )
        db.commit()
        return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer", "expires_in": expires_in}

    @staticmethod
    def _validate_user(user) -> None:
        if user.is_deleted:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account has been deleted")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")

    @staticmethod
    def _get_auth_tenant(db: Session, tenant_id: int | None) -> Tenant:
        if tenant_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not assigned to a tenant")
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant is inactive")
        if tenant.status in {"suspended", "cancelled"}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Tenant status is {tenant.status}")
        if not tenant.is_active and tenant.status != "expired":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant is inactive")
        return tenant

    @staticmethod
    def _get_latest_subscription(db: Session, tenant_id: int) -> Subscription | None:
        return db.query(Subscription).filter(
            Subscription.tenant_id == tenant_id,
        ).order_by(Subscription.id.desc()).first()

    @staticmethod
    def _subscription_is_expired(subscription: Subscription) -> bool:
        now = datetime.now(timezone.utc)
        if subscription.status == "trialing" and subscription.trial_ends_at and subscription.trial_ends_at <= now:
            return True
        if subscription.status == "active" and subscription.ends_at and subscription.ends_at <= now:
            return True
        return subscription.status == "expired"

    @staticmethod
    def _get_valid_subscription(db: Session, tenant_id: int) -> Subscription:
        subscription = db.query(Subscription).filter(
            Subscription.tenant_id == tenant_id,
            Subscription.status.in_(["trialing", "active", "past_due"]),
        ).order_by(Subscription.id.desc()).first()
        if subscription is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No active subscription")
        if AuthenticationService._subscription_is_expired(subscription):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Subscription has expired")
        return subscription

    @staticmethod
    def _get_enabled_modules(db: Session, tenant_id: int) -> list[str]:
        rows = db.query(SystemModule.code).join(TenantModule, TenantModule.module_id == SystemModule.id).filter(
            TenantModule.tenant_id == tenant_id, TenantModule.is_enabled.is_(True), SystemModule.is_active.is_(True)
        ).order_by(SystemModule.display_order.asc()).all()
        return [row[0] for row in rows]

    @staticmethod
    def _raise_invalid_credentials() -> None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect login or password", headers={"WWW-Authenticate": "Bearer"})


authentication_service = AuthenticationService()
