from fastapi import (
    Depends,
    HTTPException,
    status,
)
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.context import get_request_context
from app.database.session import get_db
from app.modules.identity.models import User
from app.modules.identity.repositories.user_repository import (
    user_repository,
)
from app.modules.identity.services.token_service import (
    token_service,
)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/identity/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    payload = token_service.decode_token(
        token,
        expected_type="access",
    )

    if payload is None:
        raise credentials_exception

    user_id = payload.get("user_id")

    if not user_id:
        raise credentials_exception

    user = user_repository.get_by_id(
        db=db,
        user_id=int(user_id),
    )

    if user is None:
        raise credentials_exception

    if user.is_deleted or not user.is_active:
        raise credentials_exception

    token_tenant_id = payload.get("tenant_id")

    if (
        not user.is_platform_admin
        and user.tenant_id != token_tenant_id
    ):
        raise credentials_exception

    # تعبئة بيانات المستخدم داخل RequestContext
    context = get_request_context()

    context.user_id = user.id
    context.tenant_id = user.tenant_id
    context.username = user.username

    return user