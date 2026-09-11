from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.enterprise.models import FixedAsset, Budget, BudgetLine, Employee, PayrollRun, PayrollLine, Project, ProjectContract
from app.modules.enterprise.schemas import AssetCreate,AssetResponse,EmployeeCreate,EmployeeResponse,PayrollRunCreate,PayrollResponse,BudgetCreate,BudgetLineCreate,BudgetResponse,ProjectCreate,ProjectResponse,ContractCreate,ContractResponse
router=APIRouter(prefix='/enterprise',tags=['Enterprise'])
def err(fn):
 try:return fn()
 except ValueError as e:raise HTTPException(400,str(e)) from e
@router.post('/assets',response_model=AssetResponse,status_code=201)
def asset(p:AssetCreate,db:Session=Depends(get_db)):
 o=FixedAsset(**p.model_dump());db.add(o);db.commit();db.refresh(o);return o
@router.get('/assets',response_model=list[AssetResponse])
def assets(company_id:int=Query(...,gt=0),db:Session=Depends(get_db)):return list(db.scalars(select(FixedAsset).where(FixedAsset.company_id==company_id).order_by(FixedAsset.code)).all())
@router.post('/assets/{asset_id}/depreciate',response_model=AssetResponse)
def depreciate(asset_id:int,company_id:int=Query(...,gt=0),months:int=Query(1,gt=0),db:Session=Depends(get_db)):
 o=db.scalar(select(FixedAsset).where(FixedAsset.id==asset_id,FixedAsset.company_id==company_id).with_for_update())
 if not o:raise HTTPException(404,'Asset not found')
 monthly=max(Decimal('0'),(Decimal(o.cost)-Decimal(o.residual_value))/o.useful_life_months); charge=min(monthly*months,Decimal(o.cost)-Decimal(o.residual_value)-Decimal(o.accumulated_depreciation));o.accumulated_depreciation+=charge;db.commit();db.refresh(o);return o
@router.post('/employees',response_model=EmployeeResponse,status_code=201)
def employee(p:EmployeeCreate,db:Session=Depends(get_db)):
 o=Employee(**p.model_dump());db.add(o);db.commit();db.refresh(o);return o
@router.get('/employees',response_model=list[EmployeeResponse])
def employees(company_id:int=Query(...,gt=0),db:Session=Depends(get_db)):return list(db.scalars(select(Employee).where(Employee.company_id==company_id,Employee.is_active.is_(True)).order_by(Employee.employee_no)).all())
@router.post('/payroll/runs',response_model=PayrollResponse,status_code=201)
def payroll(p:PayrollRunCreate,db:Session=Depends(get_db)):
 if db.scalar(select(PayrollRun).where(PayrollRun.company_id==p.company_id,PayrollRun.period==p.period)):raise HTTPException(400,'Payroll period already exists')
 emps=list(db.scalars(select(Employee).where(Employee.company_id==p.company_id,Employee.is_active.is_(True))).all());r=PayrollRun(company_id=p.company_id,period=p.period);db.add(r);db.flush();
 for e in emps:
  gross=Decimal(e.basic_salary or 0)+Decimal(e.allowances or 0);ded=Decimal(e.deductions or 0);db.add(PayrollLine(payroll_run_id=r.id,employee_id=e.id,gross=gross,deductions=ded,net=gross-ded));r.total_gross+=gross;r.total_deductions+=ded;r.total_net+=gross-ded
 r.status='posted';db.commit();db.refresh(r);return r
@router.post('/budgets',response_model=BudgetResponse,status_code=201)
def budget(p:BudgetCreate,db:Session=Depends(get_db)):
 o=Budget(**p.model_dump());db.add(o);db.commit();db.refresh(o);return o
@router.post('/budgets/{budget_id}/lines',response_model=BudgetResponse)
def budget_line(budget_id:int,p:BudgetLineCreate,db:Session=Depends(get_db)):
 o=db.get(Budget,budget_id)
 if not o:raise HTTPException(404,'Budget not found')
 if o.status!='draft':raise HTTPException(400,'Only draft budgets can be edited')
 db.add(BudgetLine(budget_id=budget_id,**p.model_dump()));db.commit();db.refresh(o);return o
@router.post('/budgets/{budget_id}/approve',response_model=BudgetResponse)
def approve_budget(budget_id:int,company_id:int=Query(...,gt=0),db:Session=Depends(get_db)):
 o=db.scalar(select(Budget).where(Budget.id==budget_id,Budget.company_id==company_id).with_for_update())
 if not o:raise HTTPException(404,'Budget not found')
 if o.status!='draft':raise HTTPException(400,'Only draft budgets can be approved')
 o.status='approved';db.commit();db.refresh(o);return o
@router.post('/projects',response_model=ProjectResponse,status_code=201)
def project(p:ProjectCreate,db:Session=Depends(get_db)):
 o=Project(**p.model_dump());db.add(o);db.commit();db.refresh(o);return o
@router.get('/projects',response_model=list[ProjectResponse])
def projects(company_id:int=Query(...,gt=0),db:Session=Depends(get_db)):return list(db.scalars(select(Project).where(Project.company_id==company_id).order_by(Project.code)).all())
@router.post('/contracts',response_model=ContractResponse,status_code=201)
def contract(p:ContractCreate,db:Session=Depends(get_db)):
 if not db.scalar(select(Project).where(Project.id==p.project_id,Project.company_id==p.company_id)):raise HTTPException(400,'Project not found')
 o=ProjectContract(**p.model_dump());db.add(o);db.commit();db.refresh(o);return o
@router.get('/contracts',response_model=list[ContractResponse])
def contracts(company_id:int=Query(...,gt=0),db:Session=Depends(get_db)):return list(db.scalars(select(ProjectContract).where(ProjectContract.company_id==company_id).order_by(ProjectContract.contract_no)).all())
