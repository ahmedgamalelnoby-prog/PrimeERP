from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import set_committed_value

from app.core.config import settings
from app.core.context import get_request_context
from app.database.session import get_db
from app.modules.identity.models import User
from app.modules.identity.repositories.user_repository import user_repository
from app.modules.identity.services.token_service import token_service
from app.modules.platform.subscriptions.service import subscription_service
from app.modules.saas.models import Tenant

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/identity/login")
TENANT_CONTEXT_HEADER = "X-Tenant-ID"


def _resolve_platform_tenant(request_context, request_tenant_id: str | None, db: Session) -> Tenant | None:
    """Resolve the tenant selected by a platform administrator for this request."""
    if not request_tenant_id:
        return None

    raw = request_tenant_id.strip()
    try:
        tenant_id = int(raw)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Tenant-ID must be a valid tenant ID") from exc

    if tenant_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Tenant-ID must be a positive tenant ID")

    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    request_context.tenant_id = tenant.id
    return tenant


def _authenticate_user(token: str, db: Session, tenant_context_header: str | None = None) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = token_service.decode_token(token, expected_type="access")
    if payload is None:
        raise credentials_exception

    user_id = payload.get("user_id")
    if not user_id:
        raise credentials_exception

    try:
        user = user_repository.get_by_id(db=db, user_id=int(user_id))
    except (TypeError, ValueError):
        raise credentials_exception
    if user is None or user.is_deleted or not user.is_active:
        raise credentials_exception

    # Role state is security state: an already-issued JWT must not keep an
    # inactive role authorized until the token expires.
    if not user.is_platform_admin and user.role_id is not None:
        from app.modules.roles.models import Role
        role = db.get(Role, user.role_id)
        if role is None or not role.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User role is inactive or unavailable")

    token_tenant_id = payload.get("tenant_id")
    if not user.is_platform_admin and user.tenant_id != token_tenant_id:
        raise credentials_exception

    context = get_request_context()
    context.user_id = user.id
    context.username = user.username

    if user.is_platform_admin:
        selected_tenant = _resolve_platform_tenant(context, tenant_context_header, db)
        if selected_tenant is not None:
            set_committed_value(user, "tenant_id", selected_tenant.id)
            set_committed_value(user, "tenant", selected_tenant)
    else:
        if user.tenant_id is None:
            raise HTTPException(status_code=403, detail="User is not assigned to a tenant")
        if tenant_context_header:
            try:
                requested_tenant_id = int(tenant_context_header.strip())
            except (TypeError, ValueError) as exc:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Tenant-ID must be a valid tenant ID") from exc
            if requested_tenant_id != user.tenant_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context does not match the authenticated user")
        context.tenant_id = user.tenant_id

    return user


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    tenant_context_header: str | None = Header(default=None, alias=TENANT_CONTEXT_HEADER),
) -> User:
    user = _authenticate_user(token, db, tenant_context_header)
    if not user.is_platform_admin:
        tenant_id = user.tenant_id
        if tenant_id is None:
            raise HTTPException(status_code=403, detail="User is not assigned to a tenant")

        tenant = db.get(Tenant, tenant_id)
        if tenant is None or not tenant.is_active or tenant.status in {"suspended", "disabled", "cancelled", "expired"}:
            raise HTTPException(status_code=402, detail="Tenant is suspended, cancelled, expired, or inactive")

        if not subscription_service(db).is_tenant_access_allowed(tenant_id):
            raise HTTPException(status_code=402, detail="Tenant subscription is expired or inactive")
    return user


def get_current_user_for_billing(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    tenant_context_header: str | None = Header(default=None, alias=TENANT_CONTEXT_HEADER),
) -> User:
    """Authenticate while allowing expired tenants to reach billing/subscription flows."""
    return _authenticate_user(token, db, tenant_context_header)
