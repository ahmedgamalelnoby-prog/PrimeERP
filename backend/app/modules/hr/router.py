from datetime import date,datetime
from decimal import Decimal
from fastapi import APIRouter,Depends,HTTPException,Query
from pydantic import BaseModel,Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models.user import User
from app.modules.enterprise.models import Employee,PayrollRun,PayrollLine
from app.modules.accounting.fiscal_years.services.fiscal_year_service import fiscal_year_service
from app.modules.accounting.journals.services.journal_service import journal_service
from app.modules.completion.domain_models import HRAttendance,HRLeave
from .models import EmploymentContract
router=APIRouter(prefix="/hr",tags=["HR"])
def scope(db,user,company_id):
    if user.tenant_id is None or db.scalar(select(Company).where(Company.id==company_id,Company.tenant_id==user.tenant_id)) is None: raise HTTPException(403,"Company is outside the current tenant")
class EmployeeIn(BaseModel):
    employee_no:str=Field(min_length=1,max_length=50);name:str=Field(min_length=1,max_length=200);department:str|None=None;job_title:str|None=None;hire_date:date;basic_salary:Decimal=Field(default=0,ge=0);allowances:Decimal=Field(default=0,ge=0);deductions:Decimal=Field(default=0,ge=0)
class ContractIn(BaseModel):
    employee_id:int;start_date:date;end_date:date|None=None;salary:Decimal=Field(default=0,ge=0);notes:str|None=None
class AttendanceIn(BaseModel):
    employee_user_id:int;work_date:date;check_in:datetime|None=None;check_out:datetime|None=None;overtime_minutes:int=Field(default=0,ge=0);status:str="present"
class LeaveIn(BaseModel):
    employee_user_id:int;start_date:date;end_date:date;leave_type:str;reason:str|None=None
class PayrollIn(BaseModel): period:str=Field(min_length=4,max_length=20)
class PayrollPostIn(BaseModel): journal_id:int=Field(gt=0);fiscal_year_id:int=Field(gt=0);period_id:int=Field(gt=0);branch_id:int=Field(gt=0);expense_account_id:int=Field(gt=0);payable_account_id:int=Field(gt=0);deduction_account_id:int=Field(gt=0);entry_number:str=Field(min_length=1,max_length=80);entry_date:date
@router.post("/employees",status_code=201)
def employee(p:EmployeeIn,company_id:int=Query(...,gt=0),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    scope(db,user,company_id);o=Employee(company_id=company_id,is_active=True,**p.model_dump());db.add(o);db.commit();db.refresh(o);return o
@router.get("/employees")
def employees(company_id:int=Query(...,gt=0),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    scope(db,user,company_id);return list(db.scalars(select(Employee).where(Employee.company_id==company_id).order_by(Employee.id)).all())
@router.post("/contracts",status_code=201)
def contract(p:ContractIn,company_id:int=Query(...,gt=0),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    scope(db,user,company_id)
    if not db.scalar(select(Employee.id).where(Employee.id==p.employee_id,Employee.company_id==company_id)):raise HTTPException(404,"Employee not found")
    o=EmploymentContract(company_id=company_id,**p.model_dump());db.add(o);db.commit();db.refresh(o);return o
@router.post("/attendance",status_code=201)
def attendance(p:AttendanceIn,company_id:int=Query(...,gt=0),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    scope(db,user,company_id)
    o=db.scalar(select(HRAttendance).where(HRAttendance.company_id==company_id,HRAttendance.employee_user_id==p.employee_user_id,HRAttendance.work_date==p.work_date))
    if o:raise HTTPException(409,"Attendance already exists")
    o=HRAttendance(tenant_id=user.tenant_id,company_id=company_id,**p.model_dump());db.add(o);db.commit();db.refresh(o);return o
@router.post("/leaves",status_code=201)
def leave(p:LeaveIn,company_id:int=Query(...,gt=0),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    scope(db,user,company_id)
    if p.end_date<p.start_date:raise HTTPException(422,"Invalid leave range")
    o=HRLeave(tenant_id=user.tenant_id,company_id=company_id,status="requested",**p.model_dump());db.add(o);db.commit();db.refresh(o);return o
@router.post("/leaves/{leave_id}/decision")
def leave_decision(leave_id:int,status:str=Query(...,pattern="^(approved|rejected|cancelled)$"),company_id:int=Query(...,gt=0),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    scope(db,user,company_id);o=db.scalar(select(HRLeave).where(HRLeave.id==leave_id,HRLeave.company_id==company_id).with_for_update())
    if not o:raise HTTPException(404,"Leave not found")
    o.status=status;o.approved_by=user.id if status=="approved" else o.approved_by;db.commit();return o
@router.post("/payroll/runs",status_code=201)
def payroll(p:PayrollIn,company_id:int=Query(...,gt=0),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    scope(db,user,company_id)
    try:
        period_date=date.fromisoformat(p.period+"-01") if len(p.period)==7 else date.fromisoformat(p.period)
    except ValueError as exc:
        raise HTTPException(422,"Payroll period must be YYYY-MM or YYYY-MM-DD") from exc
    fiscal_year_service.assert_open_for_date(db,company_id=company_id,posting_date=period_date)
    if db.scalar(select(PayrollRun.id).where(PayrollRun.company_id==company_id,PayrollRun.period==p.period)):raise HTTPException(409,"Payroll period already exists")
    emps=db.scalars(select(Employee).where(Employee.company_id==company_id,Employee.is_active.is_(True))).all()
    run=PayrollRun(company_id=company_id,period=p.period,status="draft");db.add(run);db.flush()
    gross_total=ded_total=net_total=Decimal(0)
    for e in emps:
        gross=Decimal(e.basic_salary or 0)+Decimal(e.allowances or 0);ded=Decimal(e.deductions or 0);net=gross-ded
        db.add(PayrollLine(payroll_run_id=run.id,employee_id=e.id,gross=gross,deductions=ded,net=net));gross_total+=gross;ded_total+=ded;net_total+=net
    run.total_gross=gross_total;run.total_deductions=ded_total;run.total_net=net_total;run.status="calculated";db.commit();db.refresh(run);return run
@router.post("/payroll/runs/{run_id}/post")
def post_payroll(run_id:int,p:PayrollPostIn,company_id:int=Query(...,gt=0),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    scope(db,user,company_id)
    run=db.scalar(select(PayrollRun).where(PayrollRun.id==run_id,PayrollRun.company_id==company_id).with_for_update())
    if not run: raise HTTPException(404,"Payroll run not found")
    if run.status not in {"calculated","pending_approval"}: raise HTTPException(409,"Payroll run is not ready for posting")
    if getattr(run,"journal_entry_id",None): return run
    lines=[{"account_combination_id":p.expense_account_id,"debit":run.total_gross,"credit":0,"description":f"Payroll {run.period} gross"},{"account_combination_id":p.deduction_account_id,"debit":0,"credit":run.total_deductions,"description":f"Payroll {run.period} deductions"},{"account_combination_id":p.payable_account_id,"debit":0,"credit":run.total_net,"description":f"Payroll {run.period} net payable"}]
    entry=journal_service.create_draft(db,tenant_id=user.tenant_id,company_id=company_id,branch_id=p.branch_id,journal_id=p.journal_id,fiscal_year_id=p.fiscal_year_id,period_id=p.period_id,entry_number=p.entry_number,entry_date=p.entry_date,description=f"Payroll posting {run.period}",lines=lines,user_id=user.id,source_module="hr",source_entity="payroll_run",source_id=run.id,commit=False)
    journal_service.submit(db,tenant_id=user.tenant_id,entry_id=entry.id,user_id=user.id,commit=False)
    if entry.journal.requires_approval: run.status="pending_approval"
    else:
        journal_service.post(db,tenant_id=user.tenant_id,entry_id=entry.id,user_id=user.id,commit=False); run.status="posted"
    if hasattr(run,"journal_entry_id"): run.journal_entry_id=entry.id
    db.commit();db.refresh(run);return run

@router.get("/payroll/runs/{run_id}")
def payroll_detail(run_id:int,company_id:int=Query(...,gt=0),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    scope(db,user,company_id);run=db.scalar(select(PayrollRun).where(PayrollRun.id==run_id,PayrollRun.company_id==company_id))
    if not run:raise HTTPException(404,"Payroll run not found")
    lines=list(db.scalars(select(PayrollLine).where(PayrollLine.payroll_run_id==run.id)).all())
    return {"run":run,"lines":lines,"totals":{"gross":sum((Decimal(x.gross) for x in lines),Decimal(0)),"deductions":sum((Decimal(x.deductions) for x in lines),Decimal(0)),"net":sum((Decimal(x.net) for x in lines),Decimal(0))}}
