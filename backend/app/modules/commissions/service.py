from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.commissions.models import CommissionRule, CommissionSettlement
from app.modules.commissions.schemas import CommissionCalculateRequest
from app.modules.enterprise.models import Employee


class CommissionService:
    @staticmethod
    def calculate(db: Session, company_id: int, payload: CommissionCalculateRequest) -> CommissionSettlement:
        employee = db.scalar(select(Employee).where(Employee.id == payload.employee_id, Employee.company_id == company_id, Employee.is_active.is_(True)).with_for_update())
        if employee is None:
            raise ValueError("Employee not found for company")
        rule = db.scalar(select(CommissionRule).where(CommissionRule.id == payload.rule_id, CommissionRule.company_id == company_id, CommissionRule.is_active.is_(True)).with_for_update())
        if rule is None:
            raise ValueError("Commission rule not found for company")
        base = Decimal(payload.base_amount)
        if base < Decimal(rule.min_base):
            commission = Decimal("0")
        else:
            eligible = base if rule.max_base is None else min(base, Decimal(rule.max_base))
            commission = (eligible * Decimal(rule.rate_percent) / Decimal("100")) + Decimal(rule.fixed_amount)
        commission = commission.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        existing = db.scalar(select(CommissionSettlement).where(
            CommissionSettlement.company_id == company_id,
            CommissionSettlement.employee_id == payload.employee_id,
            CommissionSettlement.rule_id == payload.rule_id,
            CommissionSettlement.period == payload.period,
            CommissionSettlement.source_type == payload.source_type,
            CommissionSettlement.source_id == payload.source_id,
        ).with_for_update())
        if existing:
            if Decimal(existing.base_amount) != base or Decimal(existing.commission_amount) != commission:
                raise ValueError("Commission source already calculated with different values")
            return existing
        settlement = CommissionSettlement(company_id=company_id, employee_id=payload.employee_id, rule_id=payload.rule_id, period=payload.period, source_type=payload.source_type, source_id=payload.source_id, base_amount=base, commission_amount=commission, notes=payload.notes)
        db.add(settlement)
        db.flush()
        return settlement


commission_service = CommissionService()
