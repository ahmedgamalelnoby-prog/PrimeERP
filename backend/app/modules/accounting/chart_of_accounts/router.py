"""HTTP API for Chart of Accounts read operations."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User

from .schemas import CostCenterResponse, DepartmentResponse, NaturalAccountResponse
from .service import ChartOfAccountsService

router = APIRouter(prefix="/chart-of-accounts", tags=["Accounting - Chart of Accounts"])


def _company_id(company_id: int, db: Session, current_user: User) -> int:
    if company_id <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="company_id must be positive")
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == current_user.tenant_id))
    if company is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company is outside the current tenant")
    if not company.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Company is inactive")
    return company_id


@router.get("/departments", response_model=list[DepartmentResponse])
def list_departments(company_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return ChartOfAccountsService.list_departments(db, _company_id(company_id, db, current_user))


@router.get("/cost-centers", response_model=list[CostCenterResponse])
def list_cost_centers(company_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return ChartOfAccountsService.list_cost_centers(db, _company_id(company_id, db, current_user))


@router.get("/natural-accounts", response_model=list[NaturalAccountResponse])
def list_natural_accounts(company_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return ChartOfAccountsService.list_natural_accounts(db, _company_id(company_id, db, current_user))
