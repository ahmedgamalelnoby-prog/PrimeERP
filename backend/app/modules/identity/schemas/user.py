from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
        examples=["ahmed"],
    )

    email: EmailStr

    full_name: str | None = Field(
        default=None,
        max_length=150,
    )

    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    address: str | None = None

    profile_image: str | None = Field(
        default=None,
        max_length=500,
    )

    preferred_language: str = Field(
        default="ar",
        min_length=2,
        max_length=5,
    )

    role_id: int | None = None


class UserCreate(UserBase):
    password: str = Field(
        min_length=8,
        max_length=128,
    )

    tenant_id: int | None = None

    is_active: bool = True
    is_superuser: bool = False
    is_platform_admin: bool = False

    must_change_password: bool = False


class UserUpdate(BaseModel):
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
    )

    email: EmailStr | None = None

    full_name: str | None = Field(
        default=None,
        max_length=150,
    )

    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    address: str | None = None

    profile_image: str | None = Field(
        default=None,
        max_length=500,
    )

    preferred_language: str | None = Field(
        default=None,
        min_length=2,
        max_length=5,
    )

    role_id: int | None = None

    is_active: bool | None = None
    is_superuser: bool | None = None
    is_platform_admin: bool | None = None
    must_change_password: bool | None = None


class UserStatusUpdate(BaseModel):
    is_active: bool


class UserPasswordReset(BaseModel):
    new_password: str = Field(
        min_length=8,
        max_length=128,
    )

    must_change_password: bool = True


class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    tenant_id: int | None

    username: str
    email: EmailStr

    full_name: str | None
    phone: str | None
    address: str | None
    profile_image: str | None
    preferred_language: str

    role_id: int | None
    role_name: str | None = None

    is_active: bool
    is_superuser: bool
    is_platform_admin: bool
    is_deleted: bool
    must_change_password: bool

    last_login: datetime | None
    created_at: datetime
    updated_at: datetime