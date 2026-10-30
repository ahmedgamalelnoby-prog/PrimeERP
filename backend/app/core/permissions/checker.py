from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context import get_optional_request_context
from app.database.session import get_db
from app.modules.branches.membership import BranchUserMembership
from app.modules.companies.membership import CompanyUserMembership
from app.modules.identity.dependencies.current_user import get_current_user
from app.modules.identity.models import User
from app.modules.roles.models import Permission, Role, role_permissions


def extract_permission_codes(current_user: Any) -> set[str]:
    """Return active permission names/codes loaded on a user or its global role."""
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


def _scoped_role_id(current_user: Any, db: Session) -> int | None:
    """Return a branch/company role override when one is assigned for this request."""
    context = get_optional_request_context()
    if context is None or context.company_id is None:
        return None

    if context.branch_id is not None:
        branch_role_id = db.scalar(
            select(BranchUserMembership.role_id).where(
                BranchUserMembership.branch_id == context.branch_id,
                BranchUserMembership.user_id == current_user.id,
                BranchUserMembership.is_active.is_(True),
                BranchUserMembership.role_id.is_not(None),
            )
        )
        if branch_role_id is not None:
            return int(branch_role_id)

    company_role_id = db.scalar(
        select(CompanyUserMembership.role_id).where(
            CompanyUserMembership.company_id == context.company_id,
            CompanyUserMembership.user_id == current_user.id,
            CompanyUserMembership.is_active.is_(True),
            CompanyUserMembership.role_id.is_not(None),
        )
    )
    return int(company_role_id) if company_role_id is not None else None


def _role_has_permission(db: Session, role_id: int, permission_code: str) -> bool:
    statement = (
        select(Permission.id)
        .join(role_permissions, role_permissions.c.permission_id == Permission.id)
        .join(Role, Role.id == role_permissions.c.role_id)
        .where(
            role_permissions.c.role_id == role_id,
            Role.is_active.is_(True),
            Permission.is_active.is_(True),
            Permission.name == permission_code,
        )
    )
    return db.scalar(statement) is not None


def user_has_permission(current_user: Any, permission_code: str, db: Session | None = None) -> bool:
    if getattr(current_user, "is_platform_admin", False) or getattr(current_user, "is_superuser", False):
        return True

    if db is not None:
        scoped_role_id = _scoped_role_id(current_user, db)
        if scoped_role_id is not None:
            # An explicit scoped role replaces (does not add to) the global role.
            return _role_has_permission(db, scoped_role_id, permission_code)

    if permission_code in extract_permission_codes(current_user):
        role = getattr(current_user, "role", None)
        if role is None or getattr(role, "is_active", True):
            return True

    if db is None or not getattr(current_user, "role_id", None):
        return False

    return _role_has_permission(db, int(current_user.role_id), permission_code)


def require_permission(permission_code: str) -> Callable[..., None]:
    """FastAPI dependency that enforces an active scoped or global role permission."""

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
