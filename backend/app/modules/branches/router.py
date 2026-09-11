from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.branches.models import Branch
from app.modules.branches.schemas import BranchCreate, BranchResponse, BranchUpdate
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.saas.entitlements import enforce_branch_limit

router = APIRouter(prefix="/branches", tags=["Branches"])


def _tenant_id(user: User) -> int:
    if user.tenant_id is None:
        raise HTTPException(status_code=403, detail="User is not assigned to a tenant")
    return user.tenant_id


def _company(db: Session, company_id: int, user: User) -> Company:
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == _tenant_id(user)))
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


def _branch(db: Session, branch_id: int, user: User) -> Branch:
    branch = db.scalar(select(Branch).where(Branch.id == branch_id, Branch.tenant_id == _tenant_id(user)))
    if branch is None:
        raise HTTPException(status_code=404, detail="Branch not found")
    return branch


@router.get("", response_model=list[BranchResponse], dependencies=[Depends(require_permission("branch.access"))])
def list_branches(company_id: int | None = Query(default=None, gt=0), active_only: bool = Query(False), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(Branch).where(Branch.tenant_id == _tenant_id(current_user)).order_by(Branch.name, Branch.id)
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
