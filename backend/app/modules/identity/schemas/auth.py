from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """
    بيانات تسجيل الدخول.

    لا يتم فرض سياسة قوة كلمة المرور هنا؛
    سياسة الطول والتعقيد تطبق عند إنشاء
    أو تغيير كلمة المرور.
    """

    login: str = Field(
        ...,
        min_length=3,
        max_length=150,
    )

    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )

    tenant_slug: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    tenant_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=200,
    )


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(
        ...,
        min_length=1,
    )


class AuthenticatedUserResponse(BaseModel):
    id: int
    tenant_id: Optional[int] = None

    username: str
    email: str
    full_name: Optional[str] = None
    role_id: Optional[int] = None

    is_active: bool
    is_superuser: bool
    is_platform_admin: bool

    preferred_language: str

    tenant_slug: Optional[str] = None
    tenant_name: Optional[str] = None
    tenant_status: Optional[str] = None
    subscription_status: Optional[str] = None

    enabled_modules: list[str] = Field(
        default_factory=list,
    )
    permissions: list[str] = Field(default_factory=list)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: AuthenticatedUserResponse