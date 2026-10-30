from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id, get_optional_request_context
from app.core.permissions import require_permission
from app.core.permissions.checker import can_assign_role
from app.database.session import get_db
from app.modules.branches.models import Branch
from app.modules.branches.membership import BranchUserMembership
from app.modules.branches.schemas import BranchCreate, BranchResponse, BranchUpdate
from app.modules.companies.models import Company
from app.modules.companies.membership import CompanyUserMembership
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.roles.models import Role
from app.modules.saas.entitlements import enforce_branch_limit
from app.modules.audit.service import record_audit_event

router = APIRouter(prefix="/branches", tags=["Branches"])


def _tenant_id(user: User) -> int:
    if get_effective_tenant_id(user) is None:
        raise HTTPException(status_code=403, detail="User is not assigned to a tenant")
    return get_effective_tenant_id(user)


def _selected_company_id() -> int:
    context = get_optional_request_context()
    company_id = context.company_id if context is not None else None
    if company_id is None:
        raise HTTPException(status_code=400, detail="Select a company using X-Company-ID before accessing branches")
    return int(company_id)


def _company(db: Session, company_id: int, user: User) -> Company:
    if company_id != _selected_company_id():
        raise HTTPException(status_code=403, detail="The requested company is not the active company")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == _tenant_id(user), Company.is_active.is_(True)))
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


def _branch_for_membership_admin(db: Session, branch_id: int, user: User) -> Branch:
    """Allow company members to administer branch grants without branch data access."""
    branch = db.scalar(select(Branch).where(
        Branch.id == branch_id,
        Branch.tenant_id == _tenant_id(user),
        Branch.company_id == _selected_company_id(),
    ))
    if branch is None:
        raise HTTPException(status_code=404, detail="Branch not found")
    if not user.is_platform_admin:
        company_membership = db.scalar(
            select(CompanyUserMembership.id).where(
                CompanyUserMembership.company_id == branch.company_id,
                CompanyUserMembership.user_id == user.id,
                CompanyUserMembership.is_active.is_(True),
            )
        )
        if company_membership is None:
            raise HTTPException(status_code=404, detail="Branch not found")
    return branch


def _branch(db: Session, branch_id: int, user: User) -> Branch:
    branch = db.scalar(select(Branch).where(
        Branch.id == branch_id,
        Branch.tenant_id == _tenant_id(user),
        Branch.company_id == _selected_company_id(),
    ))
    if branch is None:
        raise HTTPException(status_code=404, detail="Branch not found")
    if not user.is_platform_admin:
        membership = db.scalar(
            select(BranchUserMembership.id).where(
                BranchUserMembership.branch_id == branch.id,
                BranchUserMembership.user_id == user.id,
                BranchUserMembership.is_active.is_(True),
            )
        )
        if membership is None:
            raise HTTPException(status_code=404, detail="Branch not found")
    return branch


@router.get("/{branch_id}/members", dependencies=[Depends(require_permission("branch.write"))])
def list_branch_members(
    branch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    branch = _branch_for_membership_admin(db, branch_id, current_user)
    rows = db.execute(
        select(BranchUserMembership, User)
        .join(User, User.id == BranchUserMembership.user_id)
        .where(BranchUserMembership.branch_id == branch.id)
        .order_by(User.username, User.id)
    ).all()
    return [
        {
            "user_id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "user_is_active": user.is_active and not user.is_deleted,
            "membership_is_active": membership.is_active,
            "role_id": membership.role_id,
        }
        for membership, user in rows
    ]


@router.put("/{branch_id}/members/{user_id}", dependencies=[Depends(require_permission("branch.write"))])
def grant_branch_membership(
    branch_id: int,
    user_id: int,
    role_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    branch = _branch_for_membership_admin(db, branch_id, current_user)
    if role_id is not None:
        if not can_assign_role(current_user, role_id, db):
            raise HTTPException(status_code=403, detail="You cannot assign a role beyond your own permissions")
    company_membership = db.scalar(
        select(CompanyUserMembership.id).where(
            CompanyUserMembership.company_id == branch.company_id,
            CompanyUserMembership.user_id == user_id,
            CompanyUserMembership.is_active.is_(True),
        )
    )
    member_user = db.scalar(
        select(User).where(
            User.id == user_id,
            User.tenant_id == branch.tenant_id,
            User.is_deleted.is_(False),
        )
    )
    if member_user is None or company_membership is None:
        raise HTTPException(status_code=404, detail="User must have an active membership in this company")
    membership = db.scalar(
        select(BranchUserMembership).where(
            BranchUserMembership.branch_id == branch.id,
            BranchUserMembership.user_id == member_user.id,
        ).with_for_update()
    )
    if membership is None:
        membership = BranchUserMembership(
            branch_id=branch.id,
            user_id=member_user.id,
            is_active=True,
            assigned_by=current_user.id,
        )
        db.add(membership)
    else:
        membership.is_active = True
        membership.assigned_by = current_user.id
    if role_id is not None:
        membership.role_id = role_id
    db.flush()
    record_audit_event(
        db,
        action="branch.membership.grant",
        entity_type="branch_user_membership",
        entity_id=membership.id,
        user_id=current_user.id,
        tenant_id=branch.tenant_id,
        metadata={"branch_id": branch.id, "member_user_id": member_user.id},
    )
    db.commit()
    db.refresh(membership)
    return {"branch_id": branch.id, "user_id": member_user.id, "is_active": membership.is_active, "role_id": membership.role_id}


@router.delete("/{branch_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("branch.write"))])
def revoke_branch_membership(
    branch_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    branch = _branch_for_membership_admin(db, branch_id, current_user)
    membership = db.scalar(
        select(BranchUserMembership).where(
            BranchUserMembership.branch_id == branch.id,
            BranchUserMembership.user_id == user_id,
        ).with_for_update()
    )
    if membership is None:
        raise HTTPException(status_code=404, detail="Branch membership not found")
    membership.is_active = False
    record_audit_event(
        db,
        action="branch.membership.revoke",
        entity_type="branch_user_membership",
        entity_id=membership.id,
        user_id=current_user.id,
        tenant_id=branch.tenant_id,
        metadata={"branch_id": branch.id, "member_user_id": user_id},
    )
    db.commit()
    return None


@router.get("", response_model=list[BranchResponse], dependencies=[Depends(require_permission("branch.access"))])
def list_branches(company_id: int | None = Query(default=None, gt=0), active_only: bool = Query(False), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    selected_company_id = _selected_company_id()
    if company_id is not None and company_id != selected_company_id:
        raise HTTPException(status_code=403, detail="The requested company is not the active company")
    _company(db, selected_company_id, current_user)
    stmt = select(Branch).where(
        Branch.tenant_id == _tenant_id(current_user),
        Branch.company_id == selected_company_id,
    )
    if not current_user.is_platform_admin:
        stmt = stmt.join(
            BranchUserMembership,
            BranchUserMembership.branch_id == Branch.id,
        ).where(
            BranchUserMembership.user_id == current_user.id,
            BranchUserMembership.is_active.is_(True),
        )
    stmt = stmt.order_by(Branch.name, Branch.id)
    if active_only:
        stmt = stmt.where(Branch.is_active.is_(True))
    return list(db.scalars(stmt).all())


@router.get("/{branch_id}", response_model=BranchResponse, dependencies=[Depends(require_permission("branch.access"))])
def get_branch(branch_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _branch(db, branch_id, current_user)


@router.post("", response_model=BranchResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("branch.write"))])
def create_branch(payload: BranchCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company = _company(db, payload.company_id, current_user)
    enforce_branch_limit(db, company.tenant_id)
    branch = Branch(tenant_id=company.tenant_id, **payload.model_dump())
    db.add(branch)
    try:
        db.flush()
        if not current_user.is_platform_admin:
            db.add(BranchUserMembership(
                branch_id=branch.id,
                user_id=current_user.id,
                is_active=True,
                assigned_by=current_user.id,
            ))
        db.commit()
        db.refresh(branch)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Branch code already exists for this company") from exc
    return branch


@router.patch("/{branch_id}", response_model=BranchResponse, dependencies=[Depends(require_permission("branch.write"))])
def update_branch(branch_id: int, payload: BranchUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    branch = _branch(db, branch_id, current_user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(branch, field, value.strip() if isinstance(value, str) else value)
    try:
        db.commit()
        db.refresh(branch)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Branch code already exists for this company") from exc
    return branch


@router.delete("/{branch_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("branch.write"))])
def deactivate_branch(branch_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    branch = _branch(db, branch_id, current_user)
    branch.is_active = False
    db.commit()
