"""HTTP API for Chart of Accounts read operations."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db

from .schemas import (
    CostCenterResponse,
    DepartmentResponse,
    NaturalAccountResponse,
)
from .service import ChartOfAccountsService

router = APIRouter(prefix="/chart-of-accounts", tags=["Accounting - Chart of Accounts"])


def _company_id(company_id: int) -> int:
    if company_id <= 0:
        raise ValueError("company_id must be positive")
    return company_id


@router.get("/departments", response_model=list[DepartmentResponse])
def list_departments(company_id: int, db: Session = Depends(get_db)):
    return ChartOfAccountsService.list_departments(db, _company_id(company_id))


@router.get("/cost-centers", response_model=list[CostCenterResponse])
def list_cost_centers(company_id: int, db: Session = Depends(get_db)):
    return ChartOfAccountsService.list_cost_centers(db, _company_id(company_id))


@router.get("/natural-accounts", response_model=list[NaturalAccountResponse])
def list_natural_accounts(company_id: int, db: Session = Depends(get_db)):
    return ChartOfAccountsService.list_natural_accounts(db, _company_id(company_id))
