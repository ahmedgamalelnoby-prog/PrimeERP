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
from .models import Employee,EmploymentContract,Attendance,Leave,PayrollRun,PayrollLine
router=APIRouter(prefix="/hr",tags=["HR"])
def scope(db,user,company_id):
 if user.tenant_id is None or db.scalar(select(Company).where(Company.id==company_id,Company.tenant_id==user.tenant_id)) is None: raise HTTPException(403,"Company is outside the current tenant")
class EmployeeIn(BaseModel):
 employee_code:str=Field(min_length=1,max_length=50);full_name:str=Field(min_length=1,max_length=200);user_id:int|None=None;department:str|None=None;job_title:str|None=None;hire_date:date|None=None;base_salary:Decimal=Field(default=0,ge=0);bank_account:str|None=None
class ContractIn(BaseModel): employee_id:int;start_date:date;end_date:date|None=None;salary:Decimal=Field(default=0,ge=0);notes:str|None=None
class AttendanceIn(BaseModel): employee_id:int;work_date:date;check_in:datetime|None=None;check_out:datetime|None=None;status:str="present"
class LeaveIn(BaseModel): employee_id:int;start_date:date;end_date:date;leave_type:str;reason:str|None=None
class PayrollIn(BaseModel):period_start:date;period_end:date
@router.post("/employees",status_code=201)
def employee(p:EmployeeIn,company_id:int=Query(...,gt=0),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 scope(db,user,company_id);o=Employee(company_id=company_id,**p.model_dump());db.add(o);db.commit();db.refresh(o);return o
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
 if not db.scalar(select(Employee.id).where(Employee.id==p.employee_id,Employee.company_id==company_id)):raise HTTPException(404,"Employee not found")
 o=db.scalar(select(Attendance).where(Attendance.employee_id==p.employee_id,Attendance.work_date==p.work_date))
 if o: raise HTTPException(409,"Attendance already exists for employee/date")
 o=Attendance(company_id=company_id,**p.model_dump());db.add(o);db.commit();db.refresh(o);return o
@router.post("/leaves",status_code=201)
def leave(p:LeaveIn,company_id:int=Query(...,gt=0),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 scope(db,user,company_id)
 if p.end_date<p.start_date:raise HTTPException(422,"Invalid leave range")
 if not db.scalar(select(Employee.id).where(Employee.id==p.employee_id,Employee.company_id==company_id)):raise HTTPException(404,"Employee not found")
 o=Leave(company_id=company_id,status="pending",**p.model_dump());db.add(o);db.commit();db.refresh(o);return o
@router.post("/leaves/{leave_id}/decision")
def leave_decision(leave_id:int,status:str=Query(...,pattern="^(approved|rejected|cancelled)$"),company_id:int=Query(...,gt=0),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 scope(db,user,company_id);o=db.scalar(select(Leave).where(Leave.id==leave_id,Leave.company_id==company_id).with_for_update())
 if not o:raise HTTPException(404,"Leave not found")
 o.status=status;db.commit();return o
@router.post("/payroll/runs",status_code=201)
def payroll(p:PayrollIn,company_id:int=Query(...,gt=0),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 scope(db,user,company_id)
 if p.period_end<p.period_start:raise HTTPException(422,"Invalid payroll period")
 run=PayrollRun(company_id=company_id,period_start=p.period_start,period_end=p.period_end,status="draft");db.add(run);db.flush()
 emps=db.scalars(select(Employee).where(Employee.company_id==company_id,Employee.status=="active")).all()
 for e in emps:
  gross=Decimal(e.base_salary or 0);ded=Decimal(0);allow=Decimal(0);net=gross+allow-ded
  db.add(PayrollLine(payroll_run_id=run.id,employee_id=e.id,gross=gross,allowances=allow,deductions=ded,net=net,employer_cost=gross))
 run.status="calculated";db.commit();db.refresh(run);return run
@router.get("/payroll/runs/{run_id}")
def payroll_detail(run_id:int,company_id:int=Query(...,gt=0),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 scope(db,user,company_id);run=db.scalar(select(PayrollRun).where(PayrollRun.id==run_id,PayrollRun.company_id==company_id))
 if not run:raise HTTPException(404,"Payroll run not found")
 lines=list(db.scalars(select(PayrollLine).where(PayrollLine.payroll_run_id==run.id)).all())
 return {"run":run,"lines":lines,"totals":{"gross":sum((Decimal(x.gross) for x in lines),Decimal(0)),"net":sum((Decimal(x.net) for x in lines),Decimal(0)),"employer_cost":sum((Decimal(x.employer_cost) for x in lines),Decimal(0))}}
