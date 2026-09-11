from __future__ import annotations

from typing import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.identity.dependencies.current_user import get_current_user
from app.modules.identity.models import User


def require_permission(permission_name: str) -> Callable:
    """Return a FastAPI dependency enforcing an application permission.

    Platform administrators and explicit superusers bypass normal RBAC checks.
    Tenant users must have an active role containing the named active permission.
    """

    def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        if current_user.is_platform_admin or current_user.is_superuser:
            return current_user

        role = current_user.role
        if role is None or not role.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no active role",
            )

        # Use the relationship loaded from the tenant-scoped user role. The
        # permission itself must also be active before it can authorize access.
        allowed = any(
            permission.name == permission_name and permission.is_active
            for permission in role.permissions
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission_name}",
            )

        return current_user

    return dependency
