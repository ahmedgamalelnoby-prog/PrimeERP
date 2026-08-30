from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserLogin(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str


class UserLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: dict


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)

    full_name: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    phone: Optional[str] = Field(
        default=None,
        max_length=20,
    )

    address: Optional[str] = None
    role_id: Optional[int] = None

    is_active: bool = True
    is_superuser: bool = False
    must_change_password: bool = False


class UserUpdate(BaseModel):
    username: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=50,
    )

    email: Optional[EmailStr] = None

    full_name: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    phone: Optional[str] = Field(
        default=None,
        max_length=20,
    )

    address: Optional[str] = None
    role_id: Optional[int] = None

    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    must_change_password: Optional[bool] = None

    password: Optional[str] = Field(
        default=None,
        min_length=6,
        max_length=128,
    )


class UserStatusUpdate(BaseModel):
    is_active: bool


class UserPasswordReset(BaseModel):
    new_password: str = Field(
        min_length=6,
        max_length=128,
    )

    must_change_password: bool = True


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    profile_image: Optional[str] = None

    is_active: bool
    is_superuser: bool
    is_deleted: bool
    must_change_password: bool

    role_id: Optional[int] = None
    role_name: Optional[str] = None

    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChangePassword(BaseModel):
    old_password: str
    new_password: str = Field(
        min_length=6,
        max_length=128,
    )


class ResetPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordConfirm(BaseModel):
    token: str
    new_password: str = Field(
        min_length=6,
        max_length=128,
    )