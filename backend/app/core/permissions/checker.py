from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.identity.dependencies.current_user import get_current_user
from app.modules.identity.models import User
from app.modules.roles.models import Permission, role_permissions


def extract_permission_codes(current_user: Any) -> set[str]:
    """Return only active permission names/codes already loaded on a user or role."""
    permission_codes: set[str] = set()
    for owner in (current_user, getattr(current_user, "role", None)):
        for permission in getattr(owner, "permissions", None) or []:
            if isinstance(permission, str):
                permission_codes.add(permission)
                continue
            if getattr(permission, "is_active", True) is False:
                continue
            for attr in ("code", "name"):
                value = getattr(permission, attr, None)
                if value:
                    permission_codes.add(str(value))
    return permission_codes


def user_has_permission(current_user: Any, permission_code: str, db: Session | None = None) -> bool:
    if getattr(current_user, "is_platform_admin", False) or getattr(current_user, "is_superuser", False):
        return True

    if permission_code in extract_permission_codes(current_user):
        return True

    if db is None or not getattr(current_user, "role_id", None):
        return False

    statement = (
        select(Permission.id)
        .join(role_permissions, role_permissions.c.permission_id == Permission.id)
        .where(
            role_permissions.c.role_id == current_user.role_id,
            Permission.is_active.is_(True),
            Permission.name == permission_code,
        )
    )
    return db.scalar(statement) is not None


def require_permission(permission_code: str) -> Callable[..., None]:
    """FastAPI dependency that enforces a role permission at the API boundary."""

    def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> None:
        if not user_has_permission(current_user, permission_code, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission_code}",
            )

    return dependency


def require_platform_admin() -> Callable[..., None]:
    """FastAPI dependency for global platform-owned master data."""

    def dependency(current_user: User = Depends(get_current_user)) -> None:
        if not getattr(current_user, "is_platform_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Platform administrator privileges are required",
            )

    return dependency
