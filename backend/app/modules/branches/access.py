from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import HTTPException

from app.core.context import get_effective_tenant_id
from app.core.permissions.checker import user_has_permission
from app.modules.branches.models import Branch, UserBranchMembership
from app.modules.identity.models import User


def can_manage_all_branches(db: Session, user: User) -> bool:
    return bool(
        user.is_platform_admin
        or user_has_permission(user, "branch.manage_all", db)
    )


def require_branch_access(
    db: Session,
    user: User,
    branch_id: int,
    *,
    require_active: bool = True,
) -> Branch:
    tenant_id = get_effective_tenant_id(user)
    stmt = select(Branch).where(
        Branch.id == branch_id,
        Branch.tenant_id == tenant_id,
    )
    if require_active:
        stmt = stmt.where(Branch.is_active.is_(True))
    branch = db.scalar(stmt)
    if branch is None:
        raise HTTPException(status_code=404, detail="Branch not found")

    if not can_manage_all_branches(db, user):
        membership_id = db.scalar(
            select(UserBranchMembership.id).where(
                UserBranchMembership.tenant_id == tenant_id,
                UserBranchMembership.user_id == user.id,
                UserBranchMembership.branch_id == branch.id,
                UserBranchMembership.is_active.is_(True),
            )
        )
        if membership_id is None:
            raise HTTPException(
                status_code=403,
                detail="You are not assigned to this branch",
            )
    return branch


def accessible_branch_ids(db: Session, user: User) -> list[int]:
    tenant_id = get_effective_tenant_id(user)
    if can_manage_all_branches(db, user):
        return list(
            db.scalars(
                select(Branch.id).where(
                    Branch.tenant_id == tenant_id,
                    Branch.is_active.is_(True),
                )
            ).all()
        )
    return list(
        db.scalars(
            select(UserBranchMembership.branch_id)
            .join(Branch, Branch.id == UserBranchMembership.branch_id)
            .where(
                UserBranchMembership.tenant_id == tenant_id,
                UserBranchMembership.user_id == user.id,
                UserBranchMembership.is_active.is_(True),
                Branch.tenant_id == tenant_id,
                Branch.is_active.is_(True),
            )
        ).all()
    )
