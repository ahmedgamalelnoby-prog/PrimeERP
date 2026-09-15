"""HTTP API for Chart of Accounts read operations."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User

from .schemas import (
    CostCenterResponse,
    DepartmentResponse,
    NaturalAccountResponse,
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
    """Resolve the requested company only inside the user's effective tenant."""
    company_id = _company_id(company_id)
    tenant_id = get_effective_tenant_id(current_user)
    company = db.scalar(
        select(Company.id).where(
            Company.id == company_id,
            Company.tenant_id == tenant_id,
            Company.is_active.is_(True),
        )
    )
    if company is None:
        # Do not disclose whether a company exists in another tenant.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company


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
