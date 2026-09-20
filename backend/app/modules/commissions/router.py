from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.commissions.models import CommissionRule, CommissionSettlement
from app.modules.commissions.schemas import CommissionRuleCreate, CommissionRuleResponse, CommissionCalculateRequest, CommissionSettlementResponse
from app.modules.commissions.service import commission_service

router = APIRouter(prefix="/commissions", tags=["Commissions"])


def company_for_user(db: Session, company_id: int, user: User) -> Company:
    if user.tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == user.tenant_id))
    if company is None:
        raise HTTPException(404, "Company not found")
    return company


@router.post("/rules", response_model=CommissionRuleResponse, status_code=201, dependencies=[Depends(require_permission("enterprise.write"))])
def create_rule(payload: CommissionRuleCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company_for_user(db, payload.company_id, current_user)
    rule = CommissionRule(**payload.model_dump())
    db.add(rule)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Commission rule code already exists for this company")
    db.refresh(rule)
    return rule


@router.get("/rules", response_model=list[CommissionRuleResponse], dependencies=[Depends(require_permission("enterprise.access"))])
def list_rules(company_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company_for_user(db, company_id, current_user)
    return list(db.scalars(select(CommissionRule).where(CommissionRule.company_id == company_id).order_by(CommissionRule.code)).all())


@router.post("/calculate", response_model=CommissionSettlementResponse, status_code=201, dependencies=[Depends(require_permission("enterprise.post"))])
def calculate(payload: CommissionCalculateRequest, company_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company_for_user(db, company_id, current_user)
    try:
        settlement = commission_service.calculate(db, company_id, payload)
        db.commit()
        db.refresh(settlement)
        return settlement
    except ValueError as exc:
        db.rollback()
        raise HTTPException(422, str(exc))
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Commission source is already settled")


@router.post("/calculate-from-source", response_model=CommissionSettlementResponse, status_code=201, dependencies=[Depends(require_permission("enterprise.post"))])
def calculate_from_source(employee_id: int, rule_id: int, period: str, source_type: str, source_id: int, company_id: int, notes: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company_for_user(db, company_id, current_user)
    try:
        settlement = commission_service.calculate_from_source(db, company_id, employee_id=employee_id, rule_id=rule_id, period=period, source_type=source_type, source_id=source_id, notes=notes)
        db.commit()
        db.refresh(settlement)
        return settlement
    except ValueError as exc:
        db.rollback()
        raise HTTPException(422, str(exc))
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Commission source is already settled")


@router.get("/settlements", response_model=list[CommissionSettlementResponse], dependencies=[Depends(require_permission("enterprise.access"))])
def list_settlements(company_id: int, period: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company_for_user(db, company_id, current_user)
    stmt = select(CommissionSettlement).where(CommissionSettlement.company_id == company_id)
    if period:
        stmt = stmt.where(CommissionSettlement.period == period)
    return list(db.scalars(stmt.order_by(CommissionSettlement.period.desc(), CommissionSettlement.id.desc())).all())


@router.post("/settlements/{settlement_id}/approve", response_model=CommissionSettlementResponse, dependencies=[Depends(require_permission("enterprise.post"))])
def approve(settlement_id: int, company_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company_for_user(db, company_id, current_user)
    settlement = db.scalar(select(CommissionSettlement).where(CommissionSettlement.id == settlement_id, CommissionSettlement.company_id == company_id).with_for_update())
    if settlement is None:
        raise HTTPException(404, "Commission settlement not found")
    if settlement.status != "draft":
        raise HTTPException(409, "Only draft settlements can be approved")
    settlement.status = "approved"
    db.commit()
    db.refresh(settlement)
    return settlement
