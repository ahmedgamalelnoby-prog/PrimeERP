"""HTTP API for Chart of Accounts read operations."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.companies.access import require_company_access
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User

from .schemas import (
    CostCenterResponse,
    DepartmentResponse,
    NaturalAccountResponse,
    AccountCombinationListResponse,
)
from .service import ChartOfAccountsService

router = APIRouter(prefix="/chart-of-accounts", tags=["Accounting - Chart of Accounts"])


def _company_id(company_id: int) -> int:
    if company_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="company_id must be positive",
        )
    return company_id


def _authorized_company(db: Session, company_id: int, current_user: User) -> int:
    company_id = _company_id(company_id)
    return require_company_access(db, current_user, company_id, active_only=True).id


@router.get(
    "/departments",
    response_model=list[DepartmentResponse],
    dependencies=[Depends(require_permission("accounting.chart_of_accounts.read"))],
)
def list_departments(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ChartOfAccountsService.list_departments(
        db, _authorized_company(db, company_id, current_user)
    )


@router.get(
    "/cost-centers",
    response_model=list[CostCenterResponse],
    dependencies=[Depends(require_permission("accounting.chart_of_accounts.read"))],
)
def list_cost_centers(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ChartOfAccountsService.list_cost_centers(
        db, _authorized_company(db, company_id, current_user)
    )


@router.get(
    "/natural-accounts",
    response_model=list[NaturalAccountResponse],
    dependencies=[Depends(require_permission("accounting.chart_of_accounts.read"))],
)
def list_natural_accounts(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ChartOfAccountsService.list_natural_accounts(
        db, _authorized_company(db, company_id, current_user)
    )


@router.get(
    "/combinations",
    response_model=list[AccountCombinationListResponse],
    dependencies=[Depends(require_permission("accounting.chart_of_accounts.read"))],
)
def list_account_combinations(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ChartOfAccountsService.list_account_combinations(
        db, _authorized_company(db, company_id, current_user)
    )
