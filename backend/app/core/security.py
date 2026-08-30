import bcrypt

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.modules.identity.models import User
from app.modules.identity.repositories.user_repository import (
    user_repository,
)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    if not plain_password or not hashed_password:
        return False

    if not isinstance(plain_password, str):
        return False

    if not isinstance(hashed_password, str):
        return False

    try:
        password_bytes = plain_password.encode("utf-8")
        hashed_password_bytes = hashed_password.encode("utf-8")

        if len(password_bytes) > 72:
            return False

        return bcrypt.checkpw(
            password_bytes,
            hashed_password_bytes,
        )

    except (
        ValueError,
        TypeError,
        AttributeError,
    ):
        return False


def get_password_hash(
    password: str,
) -> str:
    if not isinstance(password, str):
        raise TypeError(
            "Password must be a string"
        )

    password_bytes = password.encode("utf-8")

    if len(password_bytes) > 72:
        raise ValueError(
            "Password cannot be longer than 72 bytes"
        )

    hashed_password = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt(rounds=12),
    )

    return hashed_password.decode("utf-8")


def authenticate_user(
    db: Session,
    username: str,
    password: str,
) -> Optional[User]:
    login_value = username.strip()

    user = (
        db.query(User)
        .filter(
            or_(
                User.email.ilike(login_value),
                User.username.ilike(login_value),
            )
        )
        .first()
    )

    if user is None:
        return None

    if getattr(
        user,
        "is_deleted",
        False,
    ):
        return None

    if not user.is_active:
        return None

    if not verify_password(
        password,
        user.hashed_password,
    ):
        return None

    return user


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    to_encode = data.copy()

    expire = datetime.utcnow() + (
        expires_delta
        or timedelta(
            minutes=int(
                settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        )
    )

    to_encode.update(
        {
            "exp": expire,
            "token_type": "access",
        }
    )

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_refresh_token(
    data: dict,
) -> str:
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        days=int(
            settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    )

    to_encode.update(
        {
            "exp": expire,
            "token_type": "refresh",
        }
    )

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def verify_token(
    token: str,
) -> Optional[dict]:
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[
                settings.ALGORITHM
            ],
        )

    except JWTError:
        return None


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )

    payload = verify_token(token)

    if payload is None:
        raise credentials_exception

    user_id = payload.get("user_id")

    if user_id:
        user = user_repository.get_by_id(
            db=db,
            user_id=int(user_id),
        )

    else:
        subject = payload.get("sub")

        if not subject:
            raise credentials_exception

        user = (
            db.query(User)
            .filter(
                or_(
                    User.email.ilike(
                        str(subject)
                    ),
                    User.username.ilike(
                        str(subject)
                    ),
                )
            )
            .first()
        )

    if user is None:
        raise credentials_exception

    if getattr(
        user,
        "is_deleted",
        False,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account has been deleted",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    token_tenant_id = payload.get(
        "tenant_id"
    )

    if (
        token_tenant_id is not None
        and not user.is_platform_admin
        and user.tenant_id != token_tenant_id
    ):
        raise credentials_exception

    return user