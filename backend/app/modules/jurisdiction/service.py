from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Optional
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session
from .models import CompanyJurisdiction, Jurisdiction, JurisdictionDecision, PartnerJurisdiction, TaxRule


@dataclass(frozen=True)
class JurisdictionContext:
    company_id: int
    partner_id: Optional[int]
    transaction_type: str
    transaction_date: date
    place_of_supply: Optional[str] = None
    b2b: bool = True
    goods_or_services: Optional[str] = None
    import_export: Optional[str] = None


class JurisdictionEngine:
    """Resolve tax jurisdiction from facts, never from country alone."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _active_clause(effective_date, cls):
        return and_(cls.effective_from <= effective_date, or_(cls.effective_to.is_(None), cls.effective_to >= effective_date), cls.is_active.is_(True))

    def resolve(self, ctx: JurisdictionContext) -> JurisdictionDecision:
        company_regs = self.db.scalars(select(CompanyJurisdiction).where(CompanyJurisdiction.company_id == ctx.company_id, self._active_clause(ctx.transaction_date, CompanyJurisdiction)).order_by(CompanyJurisdiction.role == "primary").with_for_update()).all()
        if not company_regs:
            raise ValueError("No active company jurisdiction is configured for the transaction date")

        partner_regs = []
        if ctx.partner_id is not None:
            partner_regs = self.db.scalars(select(PartnerJurisdiction).where(PartnerJurisdiction.partner_id == ctx.partner_id, self._active_clause(ctx.transaction_date, PartnerJurisdiction))).all()

        partner_jurisdictions = {r.jurisdiction_id for r in partner_regs}
        candidates = []
        for reg in company_regs:
            score = 0
            if reg.role == "primary": score += 20
            if reg.tax_resident: score += 10
            if ctx.place_of_supply and reg.jurisdiction_id in partner_jurisdictions and ctx.place_of_supply == "customer": score += 30
            if ctx.import_export in {"import", "export"} and reg.role in {"tax", "registration"}: score += 15
            candidates.append((score, reg))
        _, chosen = max(candidates, key=lambda x: x[0])
        jurisdiction = self.db.get(Jurisdiction, chosen.jurisdiction_id)
        if jurisdiction is None or not jurisdiction.is_active:
            raise ValueError("Resolved jurisdiction is inactive or missing")

        rule_filters = [TaxRule.jurisdiction_id == jurisdiction.id, self._active_clause(ctx.transaction_date, TaxRule), TaxRule.transaction_type.in_([ctx.transaction_type, "all"]), TaxRule.taxpayer_type.in_(["both", "b2b" if ctx.b2b else "b2c"])]
        if ctx.place_of_supply:
            rule_filters.append(TaxRule.place_of_supply.in_([ctx.place_of_supply, "any"]))
        rules = self.db.scalars(select(TaxRule).where(and_(*rule_filters)).order_by(TaxRule.priority.asc(), TaxRule.id.asc())).all()
        rationale = {"company_jurisdictions": [r.jurisdiction_id for r in company_regs], "partner_jurisdictions": sorted(partner_jurisdictions), "place_of_supply": ctx.place_of_supply, "b2b": ctx.b2b, "transaction_type": ctx.transaction_type, "transaction_date": ctx.transaction_date.isoformat()}
        decision = JurisdictionDecision(company_id=ctx.company_id, partner_id=ctx.partner_id, jurisdiction_id=jurisdiction.id, transaction_type=ctx.transaction_type, transaction_date=ctx.transaction_date, place_of_supply=ctx.place_of_supply or "company", b2b=ctx.b2b, rationale=rationale, rule_ids=[r.id for r in rules])
        self.db.add(decision)
        return decision

    def tax_rules(self, ctx: JurisdictionContext) -> list[TaxRule]:
        decision = self.resolve(ctx)
        return list(self.db.scalars(select(TaxRule).where(TaxRule.id.in_(decision.rule_ids)).order_by(TaxRule.priority.asc(), TaxRule.id.asc())).all())

    @staticmethod
    def calculate_tax(base: Decimal, rate: Decimal) -> Decimal:
        if base < 0 or rate < 0:
            raise ValueError("Tax base and rate cannot be negative")
        return (base * rate / Decimal("100")).quantize(Decimal("0.0001"))
