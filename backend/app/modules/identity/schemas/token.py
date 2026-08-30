from typing import Optional

from pydantic import BaseModel


class TokenPayload(BaseModel):
    sub: str

    user_id: int

    tenant_id: Optional[int] = None

    role_id: Optional[int] = None

    is_superuser: bool = False

    is_platform_admin: bool = False

    preferred_language: str = "ar"

    token_type: str


class TokenPairResponse(BaseModel):
    access_token: str

    refresh_token: str

    token_type: str = "bearer"

    expires_in: int