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

    @staticmethod
    def calculate_from_source(db: Session, company_id: int, *, employee_id: int, rule_id: int, period: str, source_type: str, source_id: int, notes: str | None = None) -> CommissionSettlement:
        rule = db.scalar(select(CommissionRule).where(CommissionRule.id == rule_id, CommissionRule.company_id == company_id, CommissionRule.is_active.is_(True)))
        if rule is None:
            raise ValueError("Commission rule not found for company")
        from app.modules.commerce.models import SalesDocument, CommercePayment
        source = db.scalar(select(SalesDocument).where(SalesDocument.id == source_id, SalesDocument.company_id == company_id)) if source_type in {"sale","sales_document"} else db.scalar(select(CommercePayment).where(CommercePayment.id == source_id, CommercePayment.company_id == company_id, CommercePayment.status == "posted"))
        if source is None:
            raise ValueError("Commission source not found")
        basis = rule.basis
        if source_type in {"sale","sales_document"}:
            subtotal = Decimal(source.subtotal or 0)
            gross = subtotal + Decimal(source.discount_total or 0)
            base = gross if basis == "gross_sales" else subtotal
            if basis == "collection":
                base = Decimal(source.paid_total or 0)
            if basis == "gross_profit":
                from app.modules.inventory.stock_moves.models import InventoryStockMove
                moves = db.scalars(select(InventoryStockMove).where(InventoryStockMove.company_id == company_id, InventoryStockMove.source_module == "commerce", InventoryStockMove.source_entity == "sales_delivery", InventoryStockMove.source_id.like(f"{source.id}:%"), InventoryStockMove.status == "posted")).all()
                cogs = sum((Decimal(m.quantity or 0) * Decimal(m.unit_cost or 0) for m in moves), Decimal("0"))
                base = subtotal - cogs
        elif basis == "collection":
            base = Decimal(source.amount or 0) - Decimal(source.wht_amount or 0)
        else:
            raise ValueError("This source type supports only collection basis")
        base = max(base, Decimal("0"))
        return CommissionService.calculate(db, company_id, CommissionCalculateRequest(employee_id=employee_id, rule_id=rule_id, period=period, source_type=source_type, source_id=source_id, base_amount=base, notes=notes))
    

commission_service = CommissionService()
