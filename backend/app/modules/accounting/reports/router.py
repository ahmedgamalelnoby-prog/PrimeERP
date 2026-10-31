from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.accounting.reports.schemas import FinancialSummaryResponse, TrialBalanceResponse
from app.modules.accounting.reports.service import financial_report_service
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.companies.access import has_company_access

router = APIRouter(
    prefix="/accounting/reports",
    tags=["Accounting - Financial Reports"],
    dependencies=[Depends(require_permission("accounting.access"))],
)


def tenant_id(current_user: User) -> int:
    return get_effective_tenant_id(current_user)


def authorize_company(db: Session, company_id: int, current_user: User) -> None:
    if not current_user.is_platform_admin and not has_company_access(db, current_user.id, company_id, tenant_id(current_user)):
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company is not assigned to the authenticated user")


@router.get("/trial-balance", response_model=TrialBalanceResponse)
def trial_balance(
    company_id: int = Query(gt=0),
    from_date: date | None = None,
    to_date: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    authorize_company(db, company_id, current_user)
    return financial_report_service.trial_balance(db, tenant_id=tenant_id(current_user), company_id=company_id, from_date=from_date, to_date=to_date)


@router.get("/summary", response_model=FinancialSummaryResponse)
def financial_summary(
    company_id: int = Query(gt=0),
    from_date: date | None = None,
    to_date: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    authorize_company(db, company_id, current_user)
    return financial_report_service.financial_summary(db, tenant_id=tenant_id(current_user), company_id=company_id, from_date=from_date, to_date=to_date)
