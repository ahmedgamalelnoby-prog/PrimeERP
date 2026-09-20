from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.branches.models import Branch
from app.modules.enterprise.models import FixedAsset, FixedAssetDepreciationRun, Budget, BudgetLine, Employee, PayrollRun, PayrollLine, Project, ProjectContract
from app.modules.enterprise.schemas import AssetCreate, AssetResponse, AssetDepreciateRequest, AssetDepreciationResponse, EmployeeCreate, EmployeeResponse, PayrollRunCreate, PayrollPostRequest, PayrollResponse, BudgetCreate, BudgetLineCreate, BudgetResponse, ProjectCreate, ProjectResponse, ContractCreate, ContractResponse
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.accounting.chart_of_accounts.models import AccountCombination
from app.modules.accounting.journals.models import AccountingJournal
from app.modules.commerce.models import BusinessPartner

router = APIRouter(prefix="/enterprise", tags=["Enterprise"])


def company_for_user(db: Session, company_id: int, user: User) -> Company:
    if user.tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == user.tenant_id, Company.is_active.is_(True)))
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
    account_ids={p.asset_account_id,p.accumulated_depreciation_account_id,p.depreciation_expense_account_id}
    if any(account_ids) and not all(account_ids):
        raise HTTPException(422, "Asset, accumulated depreciation, and depreciation expense accounts must be configured together")
    if all(account_ids):
        accounts=db.scalars(select(AccountCombination).where(
            AccountCombination.id.in_(account_ids),
            AccountCombination.company_id==p.company_id,
            AccountCombination.tenant_id==current_user.tenant_id,
            AccountCombination.is_active.is_(True),
        )).all()
        if len(accounts)!=3:
            raise HTTPException(422, "Fixed asset accounting accounts must belong to the selected company and tenant")
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


@router.post("/assets/{asset_id}/depreciate", response_model=AssetDepreciationResponse, status_code=201, dependencies=[Depends(require_permission("enterprise.post"))])
def depreciate(asset_id: int, p: AssetDepreciateRequest, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from calendar import monthrange
    from app.modules.accounting.fiscal_years.repositories.fiscal_year_repository import fiscal_year_repository
    from app.modules.accounting.journals.services.journal_service import journal_service
    from app.modules.accounting.journals.models import JournalEntry

    company_for_user(db, company_id, current_user)
    o = db.scalar(select(FixedAsset).where(FixedAsset.id == asset_id, FixedAsset.company_id == company_id).with_for_update())
    if not o:
        raise HTTPException(404, "Asset not found")
    if o.status != "active":
        raise HTTPException(409, "Only active assets can be depreciated")
    if not all((o.asset_account_id, o.accumulated_depreciation_account_id, o.depreciation_expense_account_id)):
        raise HTTPException(409, "Fixed asset accounting accounts must be configured before depreciation")
    posting_date = p.posting_date or date.today()
    if posting_date < o.acquisition_date:
        raise HTTPException(422, "Depreciation posting date cannot precede the acquisition date")
    existing = db.scalar(select(FixedAssetDepreciationRun).where(FixedAssetDepreciationRun.asset_id == o.id, FixedAssetDepreciationRun.posting_date == posting_date).with_for_update())
    if existing:
        raise HTTPException(409, "Depreciation has already been created for this asset and posting date")
    period = fiscal_year_repository.get_period_for_date(db, current_user.tenant_id, company_id, posting_date)
    if period is None:
        raise HTTPException(409, "No open accounting period is available for the depreciation posting date")
    period = fiscal_year_repository.get_period_by_id(db, period.id, current_user.tenant_id, for_update=True)
    if period is None or period.company_id != company_id or period.status != "open" or not period.allow_posting:
        raise HTTPException(409, "Accounting period is not open for depreciation posting")
    branch = db.scalar(select(Branch).where(Branch.id == p.branch_id, Branch.company_id == company_id, Branch.tenant_id == current_user.tenant_id, Branch.is_active.is_(True)))
    if branch is None:
        raise HTTPException(422, "Depreciation branch must belong to the selected company and tenant")
    journal = db.scalar(select(AccountingJournal).where(AccountingJournal.id == p.journal_id, AccountingJournal.tenant_id == current_user.tenant_id, AccountingJournal.company_id == company_id, AccountingJournal.is_active.is_(True)))
    if journal is None:
        raise HTTPException(422, "Depreciation journal must belong to the selected company and tenant and be active")
    account_ids={o.asset_account_id,o.accumulated_depreciation_account_id,o.depreciation_expense_account_id}
    accounts=db.scalars(select(AccountCombination).where(AccountCombination.id.in_(account_ids),AccountCombination.company_id==company_id,AccountCombination.tenant_id==current_user.tenant_id,AccountCombination.is_active.is_(True))).all()
    if len(accounts)!=len(account_ids):
        raise HTTPException(422, "Every fixed asset accounting account must belong to the selected company and tenant")
    monthly=max(Decimal("0"),(Decimal(o.cost)-Decimal(o.residual_value))/Decimal(o.useful_life_months))
    remaining=max(Decimal("0"),Decimal(o.cost)-Decimal(o.residual_value)-Decimal(o.accumulated_depreciation))
    amount=min(monthly*p.months,remaining)
    if amount <= 0:
        raise HTTPException(409, "Asset is fully depreciated")
    entry=journal_service.create_draft(
        db,tenant_id=current_user.tenant_id,company_id=company_id,branch_id=p.branch_id,journal_id=p.journal_id,
        fiscal_year_id=period.fiscal_year_id,period_id=period.id,entry_number=f"DEPR-{o.id}-{posting_date.isoformat()}",
        entry_date=posting_date,description=f"Depreciation {o.code} {posting_date.isoformat()}",
        lines=[
            {"account_combination_id":o.depreciation_expense_account_id,"debit":amount,"credit":0,"description":f"Depreciation expense {o.code}"},
            {"account_combination_id":o.accumulated_depreciation_account_id,"debit":0,"credit":amount,"description":f"Accumulated depreciation {o.code}"},
        ],
        user_id=current_user.id,source_module="enterprise",source_entity="fixed_asset_depreciation",source_id=o.id,commit=False,
    )
    journal_service.submit(db,tenant_id=current_user.tenant_id,entry_id=entry.id,user_id=current_user.id,commit=False)
    run=FixedAssetDepreciationRun(tenant_id=current_user.tenant_id,company_id=company_id,asset_id=o.id,posting_date=posting_date,months=p.months,amount=amount,journal_entry_id=entry.id,status="pending")
    db.add(run)
    if entry.journal.requires_approval:
        db.commit()
        db.refresh(run)
        return run
    journal_service.post(db,tenant_id=current_user.tenant_id,entry_id=entry.id,user_id=current_user.id,commit=False)
    o.accumulated_depreciation += amount
    run.status="posted"
    run.completed_at=datetime.now(timezone.utc)
    db.commit()
    db.refresh(run)
    return run

@router.post("/assets/{asset_id}/depreciations/{run_id}/complete", response_model=AssetDepreciationResponse, dependencies=[Depends(require_permission("enterprise.post"))])
def complete_depreciation(asset_id: int, run_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.modules.accounting.journals.models import JournalEntry
    company_for_user(db, company_id, current_user)
    run=db.scalar(select(FixedAssetDepreciationRun).where(FixedAssetDepreciationRun.id==run_id,FixedAssetDepreciationRun.asset_id==asset_id,FixedAssetDepreciationRun.company_id==company_id,FixedAssetDepreciationRun.tenant_id==current_user.tenant_id).with_for_update())
    if run is None:
        raise HTTPException(404,"Depreciation run not found")
    if run.status=="posted":
        return run
    if run.status!="pending":
        raise HTTPException(409,"Only pending depreciation runs can be completed")
    entry=db.scalar(select(JournalEntry).where(JournalEntry.id==run.journal_entry_id,JournalEntry.tenant_id==current_user.tenant_id,JournalEntry.company_id==company_id).with_for_update())
    if entry is None:
        raise HTTPException(409,"Depreciation journal entry not found")
    if entry.status!="posted":
        raise HTTPException(409,"Depreciation journal entry must be approved and posted before completing depreciation")
    asset=db.scalar(select(FixedAsset).where(FixedAsset.id==asset_id,FixedAsset.company_id==company_id).with_for_update())
    if asset is None:
        raise HTTPException(404,"Asset not found")
    remaining=max(Decimal("0"),Decimal(asset.cost)-Decimal(asset.residual_value)-Decimal(asset.accumulated_depreciation))
    if run.amount > remaining:
        raise HTTPException(409,"Depreciation run exceeds the asset's remaining depreciable value")
    asset.accumulated_depreciation += run.amount
    run.status="posted";run.completed_at=datetime.now(timezone.utc)
    db.commit();db.refresh(run)
    return run


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
    r = PayrollRun(company_id=p.company_id, period=period, total_gross=0, total_deductions=0, total_net=0, status="calculated")
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
    try:
        db.commit()
    except IntegrityError:
        rollback_integrity(db, "Payroll period already exists")
    db.refresh(r)
    return r


@router.post("/payroll/runs/{payroll_run_id}/post", response_model=PayrollResponse, dependencies=[Depends(require_permission("enterprise.post"))])
def post_payroll(
    payroll_run_id: int,
    p: PayrollPostRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from calendar import monthrange
    from app.modules.accounting.fiscal_years.repositories.fiscal_year_repository import fiscal_year_repository
    from app.modules.accounting.journals.services.journal_service import journal_service

    r = db.scalar(select(PayrollRun).where(PayrollRun.id == payroll_run_id).with_for_update())
    if r is None:
        raise HTTPException(404, "Payroll run not found")
    company_for_user(db, r.company_id, current_user)
    if r.journal_entry_id is not None or r.status == "posted":
        raise HTTPException(409, "Payroll run is already posted")
    if r.status != "calculated":
        raise HTTPException(409, "Only calculated payroll runs can be posted")

    year, month = int(r.period[:4]), int(r.period[5:])
    posting_date = date(year, month, monthrange(year, month)[1])
    period = fiscal_year_repository.get_period_for_date(
        db=db, tenant_id=current_user.tenant_id, company_id=r.company_id, posting_date=posting_date
    )
    if period is None:
        raise HTTPException(409, "No accounting period is available for the payroll posting date")
    period = fiscal_year_repository.get_period_by_id(db, period.id, current_user.tenant_id, for_update=True)
    if period is None or period.company_id != r.company_id or period.status != "open" or not period.allow_posting:
        raise HTTPException(409, "Accounting period is not open for payroll posting")

    branch = db.scalar(select(Branch).where(Branch.id == p.branch_id, Branch.company_id == r.company_id, Branch.tenant_id == current_user.tenant_id, Branch.is_active.is_(True)))
    if branch is None:
        raise HTTPException(422, "Payroll branch must belong to the selected company and tenant")

    journal = db.scalar(select(AccountingJournal).where(
        AccountingJournal.id == p.journal_id,
        AccountingJournal.tenant_id == current_user.tenant_id,
        AccountingJournal.company_id == r.company_id,
        AccountingJournal.is_active.is_(True),
    ))
    if journal is None:
        raise HTTPException(422, "Payroll journal must belong to the selected company and tenant and be active")

    account_ids = {p.expense_account_id, p.salary_payable_account_id}
    if r.total_deductions:
        if p.deductions_payable_account_id is None:
            raise HTTPException(422, "A deductions payable account is required when payroll deductions exist")
        account_ids.add(p.deductions_payable_account_id)
    accounts = db.scalars(
        select(AccountCombination).where(
            AccountCombination.id.in_(account_ids),
            AccountCombination.company_id == r.company_id,
            AccountCombination.tenant_id == current_user.tenant_id,
            AccountCombination.is_active.is_(True),
        )
    ).all()
    if len(accounts) != len(account_ids):
        raise HTTPException(422, "Every payroll posting account must belong to the selected company and tenant")

    lines = [
        {"account_combination_id": p.expense_account_id, "debit": r.total_gross, "credit": 0, "description": f"Payroll expense {r.period}"},
        {"account_combination_id": p.salary_payable_account_id, "debit": 0, "credit": r.total_net, "description": f"Net salaries payable {r.period}"},
    ]
    if r.total_deductions:
        lines.append({"account_combination_id": p.deductions_payable_account_id, "debit": 0, "credit": r.total_deductions, "description": f"Payroll deductions payable {r.period}"})

    entry = journal_service.create_draft(
        db,
        tenant_id=current_user.tenant_id,
        company_id=r.company_id,
        branch_id=p.branch_id,
        journal_id=p.journal_id,
        fiscal_year_id=period.fiscal_year_id,
        period_id=period.id,
        entry_number=f"PAYROLL-{r.period}",
        entry_date=posting_date,
        description=f"Payroll posting {r.period}",
        lines=lines,
        user_id=current_user.id,
        source_module="enterprise",
        source_entity="payroll_run",
        source_id=r.id,
        commit=False,
    )
    journal_service.submit(db, tenant_id=current_user.tenant_id, entry_id=entry.id, user_id=current_user.id, commit=False)
    if entry.journal.requires_approval:
        r.status = "pending_approval"
    else:
        journal_service.post(db, tenant_id=current_user.tenant_id, entry_id=entry.id, user_id=current_user.id, commit=False)
        r.status = "posted"
    r.journal_entry_id = entry.id
    db.commit()
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
    account = db.scalar(select(AccountCombination).where(AccountCombination.id == p.account_id, AccountCombination.tenant_id == current_user.tenant_id, AccountCombination.company_id == o.company_id, AccountCombination.is_active.is_(True)))
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
    if p.customer_id is not None:
        customer = db.scalar(select(BusinessPartner).where(
            BusinessPartner.id == p.customer_id,
            BusinessPartner.company_id == p.company_id,
            BusinessPartner.partner_type.in_(["customer", "both"]),
            BusinessPartner.is_active.is_(True),
        ))
        if customer is None:
            raise HTTPException(422, "Project customer must be an active customer of the selected company")
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
    project = db.scalar(select(Project).where(Project.id == p.project_id, Project.company_id == p.company_id))
    if project is None:
        raise HTTPException(400, "Project not found")
    if p.customer_id is not None:
        customer = db.scalar(select(BusinessPartner).where(
            BusinessPartner.id == p.customer_id,
            BusinessPartner.company_id == p.company_id,
            BusinessPartner.partner_type.in_(["customer", "both"]),
            BusinessPartner.is_active.is_(True),
        ))
        if customer is None:
            raise HTTPException(422, "Contract customer must be an active customer of the selected company")
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
    return list(db.scalars(select(ProjectContract).where(ProjectContract.company_id == company_id).order_by(ProjectContract.contract_no)).all())
