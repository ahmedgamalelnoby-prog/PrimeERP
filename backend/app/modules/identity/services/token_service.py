from datetime import (
    datetime,
    timedelta,
    timezone,
)
from typing import Any, Optional

from jose import (
    JWTError,
    jwt,
)

from app.core.config import settings
from app.modules.identity.models import User


class TokenService:
    def create_access_token(
        self,
        user: User,
    ) -> tuple[str, int]:
        expires_minutes = int(
            settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

        expires_at = (
            datetime.now(timezone.utc)
            + timedelta(
                minutes=expires_minutes
            )
        )

        payload = self._build_payload(
            user=user,
            token_type="access",
        )

        payload["exp"] = expires_at

        token = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

        return (
            token,
            expires_minutes * 60,
        )

    def create_refresh_token(
        self,
        user: User,
    ) -> str:
        expires_at = (
            datetime.now(timezone.utc)
            + timedelta(
                days=int(
                    settings
                    .REFRESH_TOKEN_EXPIRE_DAYS
                )
            )
        )

        payload = self._build_payload(
            user=user,
            token_type="refresh",
        )

        payload["exp"] = expires_at

        return jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

    def decode_token(
        self,
        token: str,
        expected_type: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[
                    settings.ALGORITHM
                ],
            )
        except JWTError:
            return None

        if (
            expected_type
            and payload.get("token_type")
            != expected_type
        ):
            return None

        return payload

    @staticmethod
    def _build_payload(
        user: User,
        token_type: str,
    ) -> dict[str, Any]:
        return {
            "sub": str(user.id),
            "user_id": user.id,
            "tenant_id": user.tenant_id,
            "role_id": user.role_id,
            "is_superuser": (
                user.is_superuser
            ),
            "is_platform_admin": (
                user.is_platform_admin
            ),
            "preferred_language": (
                user.preferred_language
            ),
            "token_type": token_type,
        }


token_service = TokenService()