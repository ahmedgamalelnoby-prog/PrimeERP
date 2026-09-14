from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional
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
    facts: Optional[dict] = None


class JurisdictionEngine:
    """Resolve jurisdiction and applicable tax rules from transaction facts."""
    def __init__(self, db: Session): self.db = db
    @staticmethod
    def _active_clause(effective_date, cls):
        return and_(cls.effective_from <= effective_date, or_(cls.effective_to.is_(None), cls.effective_to >= effective_date), cls.is_active.is_(True))
    @staticmethod
    def _condition_matches(rule: TaxRule, ctx: JurisdictionContext) -> bool:
        conditions = rule.conditions or {}
        facts = {"b2b": ctx.b2b, "goods_or_services": ctx.goods_or_services, "import_export": ctx.import_export, "place_of_supply": ctx.place_of_supply, "transaction_type": ctx.transaction_type, **(ctx.facts or {})}
        for key, expected in conditions.items():
            actual = facts.get(key)
            if isinstance(expected, dict):
                if "eq" in expected and actual != expected["eq"]: return False
                if "neq" in expected and actual == expected["neq"]: return False
                if "in" in expected and actual not in expected["in"]: return False
                if "not_in" in expected and actual in expected["not_in"]: return False
                if "gte" in expected and (actual is None or actual < expected["gte"]): return False
                if "lte" in expected and (actual is None or actual > expected["lte"]): return False
            elif actual != expected: return False
        return True
    def resolve(self, ctx: JurisdictionContext) -> JurisdictionDecision:
        company_regs = self.db.scalars(select(CompanyJurisdiction).where(CompanyJurisdiction.company_id == ctx.company_id, self._active_clause(ctx.transaction_date, CompanyJurisdiction)).with_for_update()).all()
        if not company_regs: raise ValueError("No active company jurisdiction is configured for the transaction date")
        partner_regs = []
        if ctx.partner_id is not None:
            partner_regs = self.db.scalars(select(PartnerJurisdiction).where(PartnerJurisdiction.partner_id == ctx.partner_id, self._active_clause(ctx.transaction_date, PartnerJurisdiction))).all()
        candidates = []
        for reg in company_regs:
            score = (50 if reg.role == "primary" else 30) + (10 if reg.tax_resident else 0) + (15 if reg.vat_registered else 0)
            score += 25 if ctx.place_of_supply in {"company", "origin", "local"} else 0
            score += 20 if ctx.import_export == "import" and reg.role in {"tax", "registration"} else 0
            candidates.append((score, 0, reg.jurisdiction_id))
        for reg in partner_regs:
            score = (10 if reg.tax_resident else 0) + (15 if reg.vat_registered else 0)
            score += 50 if ctx.place_of_supply in {"customer", "destination"} else 0
            score += 20 if ctx.import_export == "export" and reg.role in {"tax", "registration"} else 0
            candidates.append((score, 1, reg.jurisdiction_id))
        _, _, chosen_id = max(candidates, key=lambda item: (item[0], -item[1], -item[2]))
        jurisdiction = self.db.get(Jurisdiction, chosen_id)
        if jurisdiction is None or not jurisdiction.is_active: raise ValueError("Resolved jurisdiction is inactive or missing")
        taxpayer_type = "b2b" if ctx.b2b else "b2c"
        filters = [TaxRule.jurisdiction_id == jurisdiction.id, self._active_clause(ctx.transaction_date, TaxRule), TaxRule.transaction_type.in_([ctx.transaction_type, "all"]), TaxRule.taxpayer_type.in_(["both", taxpayer_type])]
        if ctx.place_of_supply: filters.append(TaxRule.place_of_supply.in_([ctx.place_of_supply, "any"]))
        candidate_rules = self.db.scalars(select(TaxRule).where(and_(*filters)).order_by(TaxRule.priority.asc(), TaxRule.id.asc())).all()
        rules = [r for r in candidate_rules if self._condition_matches(r, ctx)]
        rationale = {"company_jurisdictions": [r.jurisdiction_id for r in company_regs], "partner_jurisdictions": [r.jurisdiction_id for r in partner_regs], "selected_jurisdiction": jurisdiction.code, "place_of_supply": ctx.place_of_supply, "b2b": ctx.b2b, "goods_or_services": ctx.goods_or_services, "import_export": ctx.import_export, "transaction_type": ctx.transaction_type, "transaction_date": ctx.transaction_date.isoformat(), "matched_rule_count": len(rules)}
        decision = JurisdictionDecision(company_id=ctx.company_id, partner_id=ctx.partner_id, jurisdiction_id=jurisdiction.id, transaction_type=ctx.transaction_type, transaction_date=ctx.transaction_date, place_of_supply=ctx.place_of_supply or "company", b2b=ctx.b2b, rationale=rationale, rule_ids=[r.id for r in rules])
        self.db.add(decision); return decision
    def tax_rules(self, ctx: JurisdictionContext) -> list[TaxRule]:
        decision = self.resolve(ctx)
        return [] if not decision.rule_ids else list(self.db.scalars(select(TaxRule).where(TaxRule.id.in_(decision.rule_ids)).order_by(TaxRule.priority.asc(), TaxRule.id.asc())).all())
    @staticmethod
    def calculate_tax(base: Decimal, rate: Decimal) -> Decimal:
        if base < 0 or rate < 0: raise ValueError("Tax base and rate cannot be negative")
        return (base * rate / Decimal("100")).quantize(Decimal("0.0001"))


# Backward-compatible public import.
from .snapshot_service import TaxSnapshotService
