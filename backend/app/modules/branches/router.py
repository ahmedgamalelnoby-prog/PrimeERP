from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.modules.branches.access import accessible_branch_ids, can_manage_all_branches, require_branch_access
from app.database.session import get_db
from app.modules.branches.models import Branch, UserBranchMembership
from app.modules.branches.schemas import (
    BranchCreate,
    BranchMemberCreate,
    BranchMemberResponse,
    BranchResponse,
    BranchUpdate,
)
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.saas.entitlements import enforce_branch_limit

router = APIRouter(prefix="/branches", tags=["Branches"])


def _tenant_id(user: User) -> int:
    if get_effective_tenant_id(user) is None:
        raise HTTPException(status_code=403, detail="User is not assigned to a tenant")
    return get_effective_tenant_id(user)


def _company(db: Session, company_id: int, user: User) -> Company:
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == _tenant_id(user), Company.is_active.is_(True)))
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


def _branch(db: Session, branch_id: int, user: User) -> Branch:
    return require_branch_access(db, user, branch_id, require_active=False)


@router.get("", response_model=list[BranchResponse], dependencies=[Depends(require_permission("branch.access"))])
def list_branches(company_id: int | None = Query(default=None, gt=0), active_only: bool = Query(False), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(Branch).where(Branch.tenant_id == _tenant_id(current_user))
    if not can_manage_all_branches(db, current_user):
        stmt = stmt.where(Branch.id.in_(accessible_branch_ids(db, current_user)))
    stmt = stmt.order_by(Branch.name, Branch.id)
    if company_id is not None:
        _company(db, company_id, current_user)
        stmt = stmt.where(Branch.company_id == company_id)
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
        db.add(
            UserBranchMembership(
                tenant_id=branch.tenant_id,
                user_id=current_user.id,
                branch_id=branch.id,
                assigned_by_user_id=current_user.id,
                is_active=True,
            )
        )
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

@router.get(
    "/{branch_id}/members",
    response_model=list[BranchMemberResponse],
    dependencies=[Depends(require_permission("branch.access"))],
)
def list_branch_members(
    branch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    branch = _branch(db, branch_id, current_user)
    rows = db.execute(
        select(UserBranchMembership, User)
        .join(User, User.id == UserBranchMembership.user_id)
        .where(
            UserBranchMembership.tenant_id == branch.tenant_id,
            UserBranchMembership.branch_id == branch.id,
            UserBranchMembership.is_active.is_(True),
            User.is_deleted.is_(False),
        )
        .order_by(User.username, User.id)
    ).all()
    return [
        BranchMemberResponse(
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
            is_active=membership.is_active and user.is_active,
            assigned_by_user_id=membership.assigned_by_user_id,
        )
        for membership, user in rows
    ]


@router.post(
    "/{branch_id}/members",
    response_model=BranchMemberResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("branch.write"))],
)
def assign_branch_member(
    branch_id: int,
    payload: BranchMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    branch = _branch(db, branch_id, current_user)
    target_user = db.scalar(
        select(User).where(
            User.id == payload.user_id,
            User.tenant_id == branch.tenant_id,
            User.is_deleted.is_(False),
            User.is_active.is_(True),
        )
    )
    if target_user is None:
        raise HTTPException(status_code=404, detail="Active user not found in this tenant")

    membership = db.scalar(
        select(UserBranchMembership).where(
            UserBranchMembership.tenant_id == branch.tenant_id,
            UserBranchMembership.user_id == target_user.id,
            UserBranchMembership.branch_id == branch.id,
        )
    )
    if membership is None:
        membership = UserBranchMembership(
            tenant_id=branch.tenant_id,
            user_id=target_user.id,
            branch_id=branch.id,
            assigned_by_user_id=current_user.id,
            is_active=True,
        )
        db.add(membership)
    else:
        membership.is_active = True
        membership.assigned_by_user_id = current_user.id
    try:
        db.commit()
        db.refresh(membership)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Branch membership could not be saved") from exc
    return BranchMemberResponse(
        user_id=target_user.id,
        username=target_user.username,
        full_name=target_user.full_name,
        is_active=membership.is_active and target_user.is_active,
        assigned_by_user_id=membership.assigned_by_user_id,
    )


@router.delete(
    "/{branch_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("branch.write"))],
)
def revoke_branch_member(
    branch_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    branch = _branch(db, branch_id, current_user)
    membership = db.scalar(
        select(UserBranchMembership).where(
            UserBranchMembership.tenant_id == branch.tenant_id,
            UserBranchMembership.user_id == user_id,
            UserBranchMembership.branch_id == branch.id,
            UserBranchMembership.is_active.is_(True),
        )
    )
    if membership is None:
        raise HTTPException(status_code=404, detail="Active branch membership not found")
    membership.is_active = False
    db.commit()

