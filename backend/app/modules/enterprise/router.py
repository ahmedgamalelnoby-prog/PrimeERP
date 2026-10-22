from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.commerce.models import BusinessPartner
from app.modules.enterprise.models import FixedAsset, Budget, BudgetLine, Employee, PayrollRun, PayrollLine, Project, ProjectContract
from app.modules.enterprise.schemas import AssetCreate, AssetResponse, EmployeeCreate, EmployeeResponse, PayrollRunCreate, PayrollResponse, BudgetCreate, BudgetLineCreate, BudgetResponse, ProjectCreate, ProjectResponse, ContractCreate, ContractResponse
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.accounting.chart_of_accounts.models import AccountCombination
from app.modules.audit.service import record_audit_event
from app.modules.company_settings.consumers.approvals import payroll_approval_required
from app.modules.identity.models import User
from app.modules.operations.approvals.models import ApprovalRequest
from app.modules.operations.approvals.schemas import ApprovalDecision
from app.modules.operations.approvals.service import create_approval_request, decide_approval

router = APIRouter(prefix="/enterprise", tags=["Enterprise"])


class PayrollSubmit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    approver_ids: list[int] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def validate_approvers(self):
        if any(isinstance(user_id, bool) or user_id <= 0 for user_id in self.approver_ids):
            raise ValueError("Approver IDs must be positive integers")
        if len(set(self.approver_ids)) != len(self.approver_ids):
            raise ValueError("Approver IDs must be unique")
        return self


def company_for_user(db: Session, company_id: int, user: User) -> Company:
    tenant_id = get_effective_tenant_id(user)
    company = db.scalar(
        select(Company).where(
            Company.id == company_id,
            Company.tenant_id == tenant_id,
            Company.is_active.is_(True),
        )
    )
    if company is None:
        raise HTTPException(404, "Company not found")
    return company


def validate_company_customer(db: Session, company_id: int, customer_id: int | None) -> None:
    if customer_id is None:
        return
    customer = db.scalar(
        select(BusinessPartner.id).where(
            BusinessPartner.id == customer_id,
            BusinessPartner.company_id == company_id,
            BusinessPartner.partner_type.in_(("customer", "both")),
            BusinessPartner.is_active.is_(True),
        )
    )
    if customer is None:
        raise HTTPException(404, "Customer not found for this company")


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
    # Updating the asset subledger without a balanced general-ledger journal would
    # make the asset register disagree with the financial statements. The current
    # model has no depreciation expense/accumulated depreciation account mapping
    # or depreciation posting history, so fail closed until that workflow exists.
    raise HTTPException(
        409,
        "Depreciation posting is unavailable until asset accounts and a general-ledger journal workflow are configured",
    )

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
    # This endpoint calculates a payroll preview only; no approval or GL posting exists yet.
    r.status = "draft"
    try:
        db.commit()
    except IntegrityError:
        rollback_integrity(db, "Payroll period already exists")
    db.refresh(r)
    return r


@router.post(
    "/payroll/runs/{run_id}/submit",
    response_model=PayrollResponse,
    dependencies=[Depends(require_permission("enterprise.post"))],
)
def submit_payroll_run(
    run_id: int,
    payload: PayrollSubmit,
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = company_for_user(db, company_id, current_user)
    run = db.scalar(select(PayrollRun).where(
        PayrollRun.id == run_id,
        PayrollRun.company_id == company_id,
    ).with_for_update())
    if run is None:
        raise HTTPException(404, "Payroll run not found")
    if run.status != "draft":
        raise HTTPException(409, "Only draft payroll runs can be submitted")
    try:
        if payroll_approval_required(db, company_id):
            if not payload.approver_ids:
                raise HTTPException(422, "At least one payroll approver is required by company policy")
            if current_user.id in payload.approver_ids:
                raise HTTPException(422, "Payroll requester cannot approve their own payroll run")
            approvers = list(db.scalars(select(User).where(
                User.id.in_(payload.approver_ids),
                User.tenant_id == company.tenant_id,
                User.is_active.is_(True),
                User.is_deleted.is_(False),
            )).all())
            if {user.id for user in approvers} != set(payload.approver_ids):
                raise HTTPException(422, "Every payroll approver must be an active user in the current tenant")
            create_approval_request(
                db,
                tenant_id=company.tenant_id,
                company_id=company_id,
                requester_id=current_user.id,
                entity_type="payroll_run",
                entity_id=run.id,
                title=f"Payroll approval for {run.period}",
                mode="sequential",
                approver_ids=payload.approver_ids,
            )
            run.status = "pending_approval"
            action = "enterprise.payroll_submitted_for_approval"
        else:
            run.status = "ready_to_post"
            action = "enterprise.payroll_approval_not_required"
        record_audit_event(
            db,
            action=action,
            entity_type="payroll_run",
            entity_id=run.id,
            user_id=current_user.id,
            tenant_id=company.tenant_id,
            company_id=company_id,
            metadata={"period": run.period, "status": run.status},
        )
        db.commit()
        db.refresh(run)
        return run
    except HTTPException:
        db.rollback()
        raise
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc
    except Exception:
        db.rollback()
        raise


@router.post(
    "/payroll/runs/{run_id}/decision",
    response_model=PayrollResponse,
    dependencies=[Depends(require_permission("enterprise.post"))],
)
def decide_payroll_run(
    run_id: int,
    payload: ApprovalDecision,
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = company_for_user(db, company_id, current_user)
    run = db.scalar(select(PayrollRun).where(
        PayrollRun.id == run_id,
        PayrollRun.company_id == company_id,
    ).with_for_update())
    if run is None:
        raise HTTPException(404, "Payroll run not found")
    if run.status != "pending_approval":
        raise HTTPException(409, "Payroll run is not awaiting approval")
    request = db.scalar(select(ApprovalRequest).options(
        selectinload(ApprovalRequest.steps)
    ).where(
        ApprovalRequest.tenant_id == company.tenant_id,
        ApprovalRequest.company_id == company_id,
        ApprovalRequest.entity_type == "payroll_run",
        ApprovalRequest.entity_id == run.id,
        ApprovalRequest.status == "pending",
    ).with_for_update())
    if request is None:
        raise HTTPException(409, "Pending payroll approval request was not found")
    try:
        decide_approval(
            db,
            request=request,
            actor_user_id=current_user.id,
            decision=payload.decision,
            reason=payload.reason,
        )
        if request.status == "approved":
            run.status = "ready_to_post"
        elif request.status == "rejected":
            run.status = "rejected"
        record_audit_event(
            db,
            action="enterprise.payroll_approval_decided",
            entity_type="payroll_run",
            entity_id=run.id,
            user_id=current_user.id,
            tenant_id=company.tenant_id,
            company_id=company_id,
            metadata={
                "period": run.period,
                "decision": payload.decision,
                "approval_status": request.status,
                "payroll_status": run.status,
            },
        )
        db.commit()
        db.refresh(run)
        return run
    except PermissionError as exc:
        db.rollback()
        raise HTTPException(403, str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc
    except Exception:
        db.rollback()
        raise


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
    validate_company_customer(db, p.company_id, p.customer_id)
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
    validate_company_customer(db, p.company_id, p.customer_id)
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
    return list(db.scalars(select(ProjectContract).where(ProjectContract.company_id == company_id).order_by(ProjectContract.contract_no)).all())
