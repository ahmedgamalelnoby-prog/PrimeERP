from fastapi import (
    APIRouter,
    Depends,
)
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.identity.dependencies import (
    get_current_user,
)
from app.modules.identity.models import User
from app.modules.identity.schemas.auth import (
    AuthenticatedUserResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
)
from app.modules.identity.schemas.token import (
    TokenPairResponse,
)
from app.modules.identity.services.authentication_service import (
    authentication_service,
)

from app.modules.identity.api.users import (
    router as users_router,
)


router = APIRouter()


@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    return authentication_service.login(
        db=db,
        payload=payload,
    )


@router.post(
    "/refresh",
    response_model=TokenPairResponse,
)
def refresh_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    return authentication_service.refresh(
        db=db,
        refresh_token=payload.refresh_token,
    )


@router.get(
    "/me",
    response_model=AuthenticatedUserResponse,
)
def get_me(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    tenant = (
        current_user.tenant
        if current_user.tenant_id
        else None
    )

    subscription_status = None
    enabled_modules: list[str] = []

    # Platform administrators are platform-scoped and must not be blocked
    # by tenant subscription state even when a legacy tenant_id is present.
    if tenant and not current_user.is_platform_admin:
        subscription = (
            authentication_service
            ._get_valid_subscription(
                db=db,
                tenant_id=tenant.id,
            )
        )

        subscription_status = (
            subscription.status
        )

        enabled_modules = (
            authentication_service
            ._get_enabled_modules(
                db=db,
                tenant_id=tenant.id,
                plan_id=subscription.plan_id,
            )
        )

    return {
        "id": current_user.id,
        "tenant_id": current_user.tenant_id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role_id": current_user.role_id,
        "is_active": current_user.is_active,
        "is_superuser": current_user.is_superuser,
        "is_platform_admin": (
            current_user.is_platform_admin
        ),
        "preferred_language": (
            current_user.preferred_language
        ),
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
            subscription_status
        ),
        "enabled_modules": enabled_modules,
    }


router.include_router(users_router)
