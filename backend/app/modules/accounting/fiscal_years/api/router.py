from datetime import date

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.accounting.fiscal_years.schemas import AccountingPeriodCreate, AccountingPeriodResponse, FiscalYearActionRequest, FiscalYearCreate, FiscalYearResponse, FiscalYearUpdate
from app.modules.accounting.fiscal_years.services.fiscal_year_service import fiscal_year_service
from app.modules.accounting.fiscal_years.services.fiscal_close_service import fiscal_close_service
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User


router = APIRouter(
    dependencies=[Depends(require_permission("accounting.access"))],
)


@router.get("/", response_model=list[FiscalYearResponse])
def list_fiscal_years(company_id: int = Query(gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return fiscal_year_service.list_fiscal_years(db=db, company_id=company_id, current_user=current_user)


@router.post("/", response_model=FiscalYearResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("accounting.write"))])
def create_fiscal_year(payload: FiscalYearCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return fiscal_year_service.create_fiscal_year(db=db, payload=payload, current_user=current_user)


@router.get("/open-period", response_model=AccountingPeriodResponse)
def get_open_period_for_date(company_id: int = Query(gt=0), posting_date: date = Query(), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return fiscal_year_service.get_open_period_for_date(db=db, company_id=company_id, posting_date=posting_date, current_user=current_user)


@router.get("/{fiscal_year_id}", response_model=FiscalYearResponse)
def get_fiscal_year(fiscal_year_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return fiscal_year_service.get_fiscal_year(db=db, fiscal_year_id=fiscal_year_id, current_user=current_user)


@router.put("/{fiscal_year_id}", response_model=FiscalYearResponse, dependencies=[Depends(require_permission("accounting.write"))])
def update_fiscal_year(fiscal_year_id: int, payload: FiscalYearUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return fiscal_year_service.update_fiscal_year(db=db, fiscal_year_id=fiscal_year_id, payload=payload, current_user=current_user)


@router.post("/{fiscal_year_id}/periods", response_model=FiscalYearResponse, dependencies=[Depends(require_permission("accounting.write"))])
def add_accounting_period(fiscal_year_id: int, payload: AccountingPeriodCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return fiscal_year_service.add_period(db=db, fiscal_year_id=fiscal_year_id, payload=payload, current_user=current_user)


@router.post("/{fiscal_year_id}/open", response_model=FiscalYearResponse, dependencies=[Depends(require_permission("accounting.close"))])
def open_fiscal_year(fiscal_year_id: int, payload: FiscalYearActionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return fiscal_year_service.open_fiscal_year(db=db, fiscal_year_id=fiscal_year_id, current_user=current_user)


@router.post("/{fiscal_year_id}/close", response_model=FiscalYearResponse, dependencies=[Depends(require_permission("accounting.close"))])
def close_fiscal_year(fiscal_year_id: int, payload: FiscalYearActionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not payload.branch_id or not payload.journal_id or not payload.retained_earnings_account_id: raise HTTPException(status_code=422, detail="Year-end close requires branch_id, journal_id and retained_earnings_account_id")
    return fiscal_close_service.year_end_close(db,fiscal_year_id,current_user,branch_id=payload.branch_id,journal_id=payload.journal_id,retained_earnings_account_id=payload.retained_earnings_account_id,reason=payload.reason or "Year-end close")


@router.post("/periods/{period_id}/close", response_model=AccountingPeriodResponse, dependencies=[Depends(require_permission("accounting.close"))])
def close_accounting_period(period_id: int, payload: FiscalYearActionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return fiscal_close_service.close_period(db,period_id,current_user,payload.reason or "Period close")


@router.post("/periods/{period_id}/reopen", response_model=AccountingPeriodResponse, dependencies=[Depends(require_permission("accounting.close"))])
def reopen_accounting_period(period_id: int, payload: FiscalYearActionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return fiscal_close_service.privileged_reopen(db,period_id,current_user,payload.reason or "Privileged period reopen")
