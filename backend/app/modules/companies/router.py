from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.companies.schemas import CompanyCreate, CompanyResponse, CompanyUpdate
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User

router = APIRouter(prefix="/companies", tags=["Companies"])


def _tenant_id(user: User) -> int:
    if user.tenant_id is None and not user.is_platform_admin:
        raise HTTPException(status_code=403, detail="User is not assigned to a tenant")
    if user.tenant_id is None:
        raise HTTPException(status_code=400, detail="Platform admin must operate in a tenant context")
    return user.tenant_id


def _get_company(db: Session, company_id: int, user: User) -> Company:
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == _tenant_id(user)))
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.get("", response_model=list[CompanyResponse], dependencies=[Depends(require_permission("company.access"))])
def list_companies(
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Company).where(Company.tenant_id == _tenant_id(current_user)).order_by(Company.name, Company.id)
    if active_only:
        stmt = stmt.where(Company.is_active.is_(True))
    return list(db.scalars(stmt).all())


@router.get("/{company_id}", response_model=CompanyResponse, dependencies=[Depends(require_permission("company.access"))])
def get_company(company_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _get_company(db, company_id, current_user)


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("company.write"))])
def create_company(payload: CompanyCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = _tenant_id(current_user)
    company = Company(tenant_id=tenant_id, **payload.model_dump())
    db.add(company)
    try:
        db.commit()
        db.refresh(company)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Company code already exists for this tenant") from exc
    return company


@router.patch("/{company_id}", response_model=CompanyResponse, dependencies=[Depends(require_permission("company.write"))])
def update_company(company_id: int, payload: CompanyUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company = _get_company(db, company_id, current_user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(company, field, value.strip() if isinstance(value, str) else value)
    try:
        db.commit()
        db.refresh(company)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Company code already exists for this tenant") from exc
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("company.write"))])
def deactivate_company(company_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company = _get_company(db, company_id, current_user)
    company.is_active = False
    db.commit()
