from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.context import get_optional_request_context
from app.modules.audit.models import AuditEvent
from app.modules.audit.service import record_audit_event
from app.modules.identity.models.refresh_token import RefreshToken
from app.modules.identity.repositories.user_repository import user_repository
from app.modules.identity.schemas.auth import LoginRequest
from app.modules.identity.services.password_service import password_service
from app.modules.identity.services.refresh_token_service import RefreshTokenReuseError, refresh_token_service
from app.modules.identity.services.token_service import token_service
from app.modules.saas.models import Subscription, SystemModule, Tenant, TenantModule

from app.modules.saas.trial_modules import trial_modules_for_business


class AuthenticationService:
    LOGIN_WINDOW_MINUTES = 10
    LOGIN_FAILURE_LIMIT = 5
    BLOCKED_SUBSCRIPTION_STATUSES = {"cancelled", "canceled", "expired", "suspended", "past_due"}

    def login(self, db: Session, payload: LoginRequest) -> dict:
        login_key = self._login_key(payload)
        self._enforce_login_throttle(db, login_key)

        users = user_repository.find_for_login(
            db=db,
            login=payload.login,
            tenant_slug=payload.tenant_slug,
            tenant_name=payload.tenant_name,
        )
        if not users:
            self._reject_login(db, login_key, "unknown_account")
        if len(users) > 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Multiple accounts match this login. Please provide the company name.",
            )
        user = users[0]
        if not user.is_platform_admin and not payload.tenant_name:
            self._reject_login(db, login_key, "company_name_required")
        if not password_service.verify_password(payload.password, user.hashed_password):
            self._reject_login(db, login_key, "invalid_password")
        self._validate_user(user)

        tenant = None
        subscription = None
        enabled_modules: list[str] = []
        if not user.is_platform_admin:
            tenant = self._get_auth_tenant(db, user.tenant_id)
            subscription = self._get_latest_subscription(db, tenant.id)
            self._ensure_subscription_allows_login(tenant, subscription)
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

    def _login_key(self, payload: LoginRequest) -> str:
        tenant = (payload.tenant_slug or "").strip().lower()
        tenant_name = (payload.tenant_name or "").strip().lower()
        login = payload.login.strip().lower()
        return f"{tenant}:{tenant_name}:{login}"

    def _request_ip(self) -> str | None:
        context = get_optional_request_context()
        return context.ip_address if context is not None else None

    def _enforce_login_throttle(self, db: Session, login_key: str) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=self.LOGIN_WINDOW_MINUTES)
        ip_address = self._request_ip()

        account_failures = (
            db.query(func.count(AuditEvent.id))
            .filter(
                AuditEvent.action == "login.failure",
                AuditEvent.entity_type == "authentication",
                AuditEvent.entity_id == login_key,
                AuditEvent.created_at >= cutoff,
            )
            .scalar()
            or 0
        )
        ip_failures = 0
        if ip_address:
            ip_failures = (
                db.query(func.count(AuditEvent.id))
                .filter(
                    AuditEvent.action == "login.failure",
                    AuditEvent.entity_type == "authentication",
                    AuditEvent.ip_address == ip_address,
                    AuditEvent.created_at >= cutoff,
                )
                .scalar()
                or 0
            )

        if account_failures >= self.LOGIN_FAILURE_LIMIT or ip_failures >= self.LOGIN_FAILURE_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Try again later.",
                headers={"Retry-After": str(self.LOGIN_WINDOW_MINUTES * 60)},
            )

    def _reject_login(self, db: Session, login_key: str, reason: str) -> None:
        record_audit_event(
            db,
            action="login.failure",
            entity_type="authentication",
            entity_id=login_key,
            ip_address=self._request_ip(),
            metadata={"reason": reason},
        )
        db.commit()
        self._raise_invalid_credentials()

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
            self._ensure_subscription_allows_login(tenant, subscription)

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
        if tenant.status in {"suspended", "cancelled", "canceled", "expired", "disabled"}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant account is inactive or suspended")
        if not tenant.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant is inactive")
        now = datetime.now(timezone.utc)
        if tenant.is_trial and tenant.trial_ends_at is not None:
            trial_end = tenant.trial_ends_at
            if trial_end.tzinfo is None:
                trial_end = trial_end.replace(tzinfo=timezone.utc)
            if trial_end <= now:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Trial period has expired. Please activate a subscription to continue.")
        return tenant

    @staticmethod
    def _get_latest_subscription(db: Session, tenant_id: int) -> Subscription | None:
        return db.query(Subscription).filter(
            Subscription.tenant_id == tenant_id,
        ).order_by(Subscription.starts_at.desc(), Subscription.id.desc()).first()

    @classmethod
    def _subscription_is_expired(cls, subscription: Subscription) -> bool:
        now = datetime.now(timezone.utc)
        trial_ends_at = subscription.trial_ends_at
        ends_at = subscription.ends_at
        if trial_ends_at is not None and trial_ends_at.tzinfo is None:
            trial_ends_at = trial_ends_at.replace(tzinfo=timezone.utc)
        if ends_at is not None and ends_at.tzinfo is None:
            ends_at = ends_at.replace(tzinfo=timezone.utc)
        if subscription.status == "trialing" and trial_ends_at and trial_ends_at <= now:
            return True
        if subscription.status == "active" and ends_at and ends_at <= now:
            return True
        return subscription.status in cls.BLOCKED_SUBSCRIPTION_STATUSES

    @classmethod
    def _ensure_subscription_allows_login(cls, tenant: Tenant, subscription: Subscription | None) -> None:
        if subscription is None:
            return
        if cls._subscription_is_expired(subscription):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Subscription is not active. Please renew your subscription to continue.",
            )

    @staticmethod
    def _get_valid_subscription(db: Session, tenant_id: int) -> Subscription:
        subscription = db.query(Subscription).filter(
            Subscription.tenant_id == tenant_id,
            Subscription.status.in_(["trialing", "active", "past_due"]),
        ).order_by(Subscription.starts_at.desc(), Subscription.id.desc()).first()
        if subscription is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No active subscription")
        if AuthenticationService._subscription_is_expired(subscription):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Subscription has expired")
        return subscription

    @staticmethod
    def _get_enabled_modules(db: Session, tenant_id: int) -> list[str]:
        tenant = db.get(Tenant, tenant_id)
        rows = db.query(SystemModule.code).join(TenantModule, TenantModule.module_id == SystemModule.id).filter(
            TenantModule.tenant_id == tenant_id, TenantModule.is_enabled.is_(True), SystemModule.is_active.is_(True)
        ).order_by(SystemModule.display_order.asc()).all()
        enabled = [row[0] for row in rows]
        if tenant is not None and tenant.is_trial:
            allowed = trial_modules_for_business(tenant.business_type)
            enabled = [code for code in enabled if code in allowed]
        return enabled

    @staticmethod
    def _raise_invalid_credentials() -> None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect login or password", headers={"WWW-Authenticate": "Bearer"})


authentication_service = AuthenticationService()
