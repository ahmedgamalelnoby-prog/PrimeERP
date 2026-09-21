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
    if db.scalar(select(PayrollRun.id).where(PayrollRun.company_id==company_id,PayrollRun.period==p.period)):raise HTTPException(409,"Payroll period already exists")
    emps=db.scalars(select(Employee).where(Employee.company_id==company_id,Employee.is_active.is_(True))).all()
    run=PayrollRun(company_id=company_id,period=p.period,status="draft");db.add(run);db.flush()
    gross_total=ded_total=net_total=Decimal(0)
    for e in emps:
        gross=Decimal(e.basic_salary or 0)+Decimal(e.allowances or 0);ded=Decimal(e.deductions or 0);net=gross-ded
        db.add(PayrollLine(payroll_run_id=run.id,employee_id=e.id,gross=gross,deductions=ded,net=net));gross_total+=gross;ded_total+=ded;net_total+=net
    run.total_gross=gross_total;run.total_deductions=ded_total;run.total_net=net_total;run.status="calculated";db.commit();db.refresh(run);return run
@router.get("/payroll/runs/{run_id}")
def payroll_detail(run_id:int,company_id:int=Query(...,gt=0),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    scope(db,user,company_id);run=db.scalar(select(PayrollRun).where(PayrollRun.id==run_id,PayrollRun.company_id==company_id))
    if not run:raise HTTPException(404,"Payroll run not found")
    lines=list(db.scalars(select(PayrollLine).where(PayrollLine.payroll_run_id==run.id)).all())
    return {"run":run,"lines":lines,"totals":{"gross":sum((Decimal(x.gross) for x in lines),Decimal(0)),"deductions":sum((Decimal(x.deductions) for x in lines),Decimal(0)),"net":sum((Decimal(x.net) for x in lines),Decimal(0))}}
