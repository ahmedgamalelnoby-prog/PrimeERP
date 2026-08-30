from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class PermissionBase(BaseModel):
    name: str = Field(
        min_length=3,
        max_length=100,
    )

    resource: str = Field(
        min_length=2,
        max_length=100,
    )

    action: str = Field(
        min_length=2,
        max_length=50,
    )

    description: Optional[str] = Field(
        default=None,
        max_length=255,
    )

    is_active: bool = True


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(BaseModel):
    name: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=100,
    )

    resource: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    action: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=50,
    )

    description: Optional[str] = Field(
        default=None,
        max_length=255,
    )

    is_active: Optional[bool] = None


class PermissionResponse(PermissionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True
    )


class RoleBase(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=50,
    )

    description: Optional[str] = Field(
        default=None,
        max_length=255,
    )

    is_active: bool = True


class RoleCreate(RoleBase):
    permission_ids: list[int] = Field(
        default_factory=list
    )


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=50,
    )

    description: Optional[str] = Field(
        default=None,
        max_length=255,
    )

    is_active: Optional[bool] = None

    permission_ids: Optional[list[int]] = None


class RoleStatusUpdate(BaseModel):
    is_active: bool


class RolePermissionsUpdate(BaseModel):
    permission_ids: list[int] = Field(
        default_factory=list
    )


class RoleResponse(RoleBase):
    id: int
    permissions: list[PermissionResponse] = Field(
        default_factory=list
    )

    users_count: int = 0

    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True
    )