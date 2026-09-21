from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.accounting.fiscal_years.services.fiscal_close_service import fiscal_close_service

router=APIRouter(prefix="/accounting/fiscal-close",tags=["Fiscal Year Close"],dependencies=[Depends(require_permission("accounting.close"))])

@router.get("/{fiscal_year_id}/checklist")
def checklist(fiscal_year_id:int,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    return fiscal_close_service.checklist(db,company_id,fiscal_year_id,current_user)

@router.post("/periods/{period_id}/close")
def close_period(period_id:int,reason:str=Query(...,min_length=1),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    return fiscal_close_service.close_period(db,period_id,current_user,reason)

@router.post("/periods/{period_id}/reopen")
def privileged_reopen_period(period_id:int,reason:str=Query(...,min_length=1),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    return fiscal_close_service.privileged_reopen(db,period_id,current_user,reason)

@router.post("/{fiscal_year_id}/reopen")
def privileged_reopen_fiscal_year(fiscal_year_id:int,reason:str=Query(...,min_length=1),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    return fiscal_close_service.privileged_reopen_fiscal_year(db,fiscal_year_id,current_user,reason)

@router.post("/{fiscal_year_id}/year-end-close")
def year_end_close(fiscal_year_id:int,branch_id:int=Query(...,gt=0),journal_id:int=Query(...,gt=0),retained_earnings_account_id:int=Query(...,gt=0),reason:str=Query(...,min_length=1),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    return fiscal_close_service.year_end_close(db,fiscal_year_id,current_user,branch_id=branch_id,journal_id=journal_id,retained_earnings_account_id=retained_earnings_account_id,reason=reason)

@router.get("/{fiscal_year_id}/audit")
def audit(fiscal_year_id:int,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    fiscal_close_service._scope(db,company_id,current_user)
    from sqlalchemy import select
    from app.modules.accounting.fiscal_years.models.close_control import FiscalYearCloseAudit
    return db.scalars(select(FiscalYearCloseAudit).where(FiscalYearCloseAudit.tenant_id==current_user.tenant_id,FiscalYearCloseAudit.company_id==company_id,FiscalYearCloseAudit.fiscal_year_id==fiscal_year_id).order_by(FiscalYearCloseAudit.created_at.desc())).all()
