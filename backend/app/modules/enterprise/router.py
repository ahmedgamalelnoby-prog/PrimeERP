from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.enterprise.models import FixedAsset, Budget, BudgetLine, Employee, PayrollRun, PayrollLine, Project, ProjectContract
from app.modules.enterprise.schemas import AssetCreate, AssetResponse, EmployeeCreate, EmployeeResponse, PayrollRunCreate, PayrollResponse, BudgetCreate, BudgetLineCreate, BudgetResponse, ProjectCreate, ProjectResponse, ContractCreate, ContractResponse
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.accounting.chart_of_accounts.models import AccountCombination

router = APIRouter(prefix="/enterprise", tags=["Enterprise"])


def company_for_user(db: Session, company_id: int, user: User) -> Company:
    if user.tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == user.tenant_id))
    if company is None:
        raise HTTPException(404, "Company not found")
    return company


def rollback_integrity(db: Session, message: str) -> None:
    db.rollback()
    raise HTTPException(409, message)


@router.post("/assets", response_model=AssetResponse, status_code=201, dependencies=[Depends(require_permission("enterprise.write"))])
def asset(p: AssetCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company_for_user(db, p.company_id, current_user)
    if p.residual_value > p.cost:
        raise HTTPException(422, "Residual value cannot exceed asset cost")
    o = FixedAsset(**p.model_dump())
    db.add(o)
    try:
        db.commit()
    except IntegrityError:
        rollback_integrity(db, "Asset code already exists for this company")
    db.refresh(o)
    return o


@router.get("/assets", response_model=list[AssetResponse], dependencies=[Depends(require_permission("enterprise.access"))])
def assets(company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company_for_user(db, company_id, current_user)
    return list(db.scalars(select(FixedAsset).where(FixedAsset.company_id == company_id).order_by(FixedAsset.code)).all())


@router.post("/assets/{asset_id}/depreciate", response_model=AssetResponse, dependencies=[Depends(require_permission("enterprise.post"))])
def depreciate(asset_id: int, company_id: int = Query(..., gt=0), months: int = Query(1, gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company_for_user(db, company_id, current_user)
    o = db.scalar(select(FixedAsset).where(FixedAsset.id == asset_id, FixedAsset.company_id == company_id).with_for_update())
    if not o:
        raise HTTPException(404, "Asset not found")
    if o.status != "active":
        raise HTTPException(409, "Only active assets can be depreciated")
    monthly = max(Decimal("0"), (Decimal(o.cost) - Decimal(o.residual_value)) / Decimal(o.useful_life_months))
    remaining = max(Decimal("0"), Decimal(o.cost) - Decimal(o.residual_value) - Decimal(o.accumulated_depreciation))
    o.accumulated_depreciation += min(monthly * months, remaining)
    db.commit()
    db.refresh(o)
    return o


@router.post("/employees", response_model=EmployeeResponse, status_code=201, dependencies=[Depends(require_permission("enterprise.write"))])
def employee(p: EmployeeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company_for_user(db, p.company_id, current_user)
    o = Employee(**p.model_dump())
    db.add(o)
    try:
        db.commit()
    except IntegrityError:
        rollback_integrity(db, "Employee number already exists for this company")
    db.refresh(o)
    return o


@router.get("/employees", response_model=list[EmployeeResponse], dependencies=[Depends(require_permission("enterprise.access"))])
def employees(company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company_for_user(db, company_id, current_user)
    return list(db.scalars(select(Employee).where(Employee.company_id == company_id, Employee.is_active.is_(True)).order_by(Employee.employee_no)).all())


@router.post("/payroll/runs", response_model=PayrollResponse, status_code=201, dependencies=[Depends(require_permission("enterprise.post"))])
def payroll(p: PayrollRunCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company_for_user(db, p.company_id, current_user)
    period = p.period.strip()
    if len(period) != 7 or period[4] != "-" or not period[:4].isdigit() or not period[5:].isdigit() or not 1 <= int(period[5:]) <= 12:
        raise HTTPException(422, "Payroll period must use YYYY-MM format")
    existing = db.scalar(select(PayrollRun).where(PayrollRun.company_id == p.company_id, PayrollRun.period == period).with_for_update())
    if existing:
        raise HTTPException(409, "Payroll period already exists")
    emps = list(db.scalars(select(Employee).where(Employee.company_id == p.company_id, Employee.is_active.is_(True))).all())
    r = PayrollRun(company_id=p.company_id, period=period, total_gross=0, total_deductions=0, total_net=0)
    db.add(r)
    db.flush()
    gross_total = ded_total = net_total = Decimal("0")
    for e in emps:
        gross = Decimal(e.basic_salary or 0) + Decimal(e.allowances or 0)
        ded = Decimal(e.deductions or 0)
        if ded > gross:
            db.rollback()
            raise HTTPException(422, f"Employee {e.employee_no} deductions exceed gross salary")
        net = gross - ded
        db.add(PayrollLine(payroll_run_id=r.id, employee_id=e.id, gross=gross, deductions=ded, net=net))
        gross_total += gross
        ded_total += ded
        net_total += net
    r.total_gross = gross_total
    r.total_deductions = ded_total
    r.total_net = net_total
    r.status = "posted"
    try:
        db.commit()
    except IntegrityError:
        rollback_integrity(db, "Payroll period already exists")
    db.refresh(r)
    return r


@router.post("/budgets", response_model=BudgetResponse, status_code=201, dependencies=[Depends(require_permission("enterprise.write"))])
def budget(p: BudgetCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company_for_user(db, p.company_id, current_user)
    o = Budget(**p.model_dump())
    db.add(o)
    try:
        db.commit()
    except IntegrityError:
        rollback_integrity(db, "Budget with the same name already exists for this company and fiscal year")
    db.refresh(o)
    return o


@router.post("/budgets/{budget_id}/lines", response_model=BudgetResponse, dependencies=[Depends(require_permission("enterprise.write"))])
def budget_line(budget_id: int, p: BudgetLineCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    o = db.scalar(select(Budget).where(Budget.id == budget_id).with_for_update())
    if not o:
        raise HTTPException(404, "Budget not found")
    company_for_user(db, o.company_id, current_user)
    if o.status != "draft":
        raise HTTPException(400, "Only draft budgets can be edited")
    account = db.scalar(select(AccountCombination).where(AccountCombination.id == p.account_id, AccountCombination.company_id == o.company_id, AccountCombination.is_active.is_(True)))
    if not account:
        raise HTTPException(400, "Account is not valid for this company")
    line = BudgetLine(budget_id=budget_id, **p.model_dump())
    db.add(line)
    try:
        db.commit()
    except IntegrityError:
        rollback_integrity(db, "Budget already contains this account for the selected period")
    db.refresh(o)
    return o


@router.post("/budgets/{budget_id}/approve", response_model=BudgetResponse, dependencies=[Depends(require_permission("enterprise.post"))])
def approve_budget(budget_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company_for_user(db, company_id, current_user)
    o = db.scalar(select(Budget).where(Budget.id == budget_id, Budget.company_id == company_id).with_for_update())
    if not o:
        raise HTTPException(404, "Budget not found")
    if o.status != "draft":
        raise HTTPException(400, "Only draft budgets can be approved")
    if not db.scalar(select(BudgetLine.id).where(BudgetLine.budget_id == o.id).limit(1)):
        raise HTTPException(400, "Budget must contain at least one line")
    o.status = "approved"
    db.commit()
    db.refresh(o)
    return o


@router.post("/projects", response_model=ProjectResponse, status_code=201, dependencies=[Depends(require_permission("enterprise.write"))])
def project(p: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company_for_user(db, p.company_id, current_user)
    if p.end_date and p.start_date and p.end_date < p.start_date:
        raise HTTPException(422, "Project end date cannot precede start date")
    o = Project(**p.model_dump())
    db.add(o)
    try:
        db.commit()
    except IntegrityError:
        rollback_integrity(db, "Project code already exists for this company")
    db.refresh(o)
    return o


@router.get("/projects", response_model=list[ProjectResponse], dependencies=[Depends(require_permission("enterprise.access"))])
def projects(company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company_for_user(db, company_id, current_user)
    return list(db.scalars(select(Project).where(Project.company_id == company_id).order_by(Project.code)).all())


@router.post("/contracts", response_model=ContractResponse, status_code=201, dependencies=[Depends(require_permission("enterprise.write"))])
def contract(p: ContractCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company_for_user(db, p.company_id, current_user)
    if p.end_date and p.start_date and p.end_date < p.start_date:
        raise HTTPException(422, "Contract end date cannot precede start date")
    if not db.scalar(select(Project).where(Project.id == p.project_id, Project.company_id == p.company_id)):
        raise HTTPException(400, "Project not found")
    o = ProjectContract(**p.model_dump())
    db.add(o)
    try:
        db.commit()
    except IntegrityError:
        rollback_integrity(db, "Contract number already exists for this company")
    db.refresh(o)
    return o


@router.get("/contracts", response_model=list[ContractResponse], dependencies=[Depends(require_permission("enterprise.access"))])
def contracts(company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company_for_user(db, company_id, current_user)
    return list(db.scalars(select(ProjectContract).where(ProjectContract.company_id == company_id).order_by(ProjectContract.contract_no)).all()
