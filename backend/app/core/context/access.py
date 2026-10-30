"""Shared request-scope access guards for company and branch data."""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id, get_optional_request_context
from app.modules.branches.membership import BranchUserMembership
from app.modules.branches.models import Branch
from app.modules.companies.membership import CompanyUserMembership
from app.modules.companies.models import Company


def require_company_access(
    db: Session,
    company_id: int,
    user,
    *,
    require_selected: bool = True,
) -> Company:
    """Validate tenant ownership, active selection, and company membership."""
    tenant_id = get_effective_tenant_id(user)
    context = get_optional_request_context()
    if require_selected and (context is None or context.company_id != company_id):
        raise HTTPException(403, "Select this company using X-Company-ID before accessing its data")
    company = db.scalar(
        select(Company).where(
            Company.id == company_id,
            Company.tenant_id == tenant_id,
            Company.is_active.is_(True),
        )
    )
    if company is None:
        raise HTTPException(404, "Company not found")
    if not getattr(user, "is_platform_admin", False):
        membership = db.scalar(
            select(CompanyUserMembership.id).where(
                CompanyUserMembership.company_id == company_id,
                CompanyUserMembership.user_id == user.id,
                CompanyUserMembership.is_active.is_(True),
            )
        )
        if membership is None:
            raise HTTPException(404, "Company not found")
    return company


def require_branch_access(
    db: Session,
    company_id: int,
    branch_id: int,
    user,
    *,
    require_selected: bool = True,
) -> Branch:
    """Validate branch ownership, active selection, and branch membership."""
    require_company_access(db, company_id, user)
    context = get_optional_request_context()
    if require_selected and (context is None or context.branch_id != branch_id):
        raise HTTPException(403, "Select this branch using X-Branch-ID before accessing its data")
    branch = db.scalar(
        select(Branch).where(
            Branch.id == branch_id,
            Branch.company_id == company_id,
            Branch.is_active.is_(True),
        )
    )
    if branch is None:
        raise HTTPException(404, "Branch not found")
    if not getattr(user, "is_platform_admin", False):
        membership = db.scalar(
            select(BranchUserMembership.id).where(
                BranchUserMembership.branch_id == branch_id,
                BranchUserMembership.user_id == user.id,
                BranchUserMembership.is_active.is_(True),
            )
        )
        if membership is None:
            raise HTTPException(404, "Branch not found")
    return branch
