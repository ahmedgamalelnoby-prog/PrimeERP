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
    """Resolve tax jurisdiction from explicit transaction facts.

    The engine fails closed when the available facts do not identify one
    defensible jurisdiction; it never silently chooses a jurisdiction by id.
    """
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _active_clause(effective_date, cls):
        return and_(
            cls.effective_from <= effective_date,
            or_(cls.effective_to.is_(None), cls.effective_to >= effective_date),
            cls.is_active.is_(True),
        )

    @staticmethod
    def _validate_context(ctx: JurisdictionContext) -> None:
        if not ctx.transaction_type:
            raise ValueError("Transaction type is required for jurisdiction resolution")
        if ctx.transaction_date is None:
            raise ValueError("Transaction date is required for jurisdiction resolution")
        if ctx.place_of_supply is None:
            raise ValueError("Place of supply is required for jurisdiction resolution")
        if ctx.goods_or_services not in {"goods", "services"}:
            raise ValueError("goods_or_services must be explicitly 'goods' or 'services'")
        if ctx.import_export not in {None, "import", "export", "domestic"}:
            raise ValueError("import_export must be import, export, domestic, or null")

    @staticmethod
    def _condition_matches(rule: TaxRule, ctx: JurisdictionContext) -> bool:
        conditions = rule.conditions or {}
        facts = {
            "b2b": ctx.b2b,
            "goods_or_services": ctx.goods_or_services,
            "import_export": ctx.import_export,
            "place_of_supply": ctx.place_of_supply,
            "transaction_type": ctx.transaction_type,
            **(ctx.facts or {}),
        }
        for key, expected in conditions.items():
            actual = facts.get(key)
            if isinstance(expected, dict):
                if "eq" in expected and actual != expected["eq"]:
                    return False
                if "neq" in expected and actual == expected["neq"]:
                    return False
                if "in" in expected and actual not in expected["in"]:
                    return False
                if "not_in" in expected and actual in expected["not_in"]:
                    return False
                if "gte" in expected and (actual is None or actual < expected["gte"]):
                    return False
                if "lte" in expected and (actual is None or actual > expected["lte"]):
                    return False
            elif actual != expected:
                return False
        return True

    @staticmethod
    def _candidate_score(reg, *, side: str, ctx: JurisdictionContext) -> int:
        score = 0
        if reg.role in {"primary", "registration"}:
            score += 40
        elif reg.role in {"tax", "permanent_establishment", "establishment"}:
            score += 30
        if reg.tax_resident:
            score += 10
        if reg.vat_registered:
            score += 10
        if side == "company" and ctx.place_of_supply in {"company", "origin", "local"}:
            score += 30
        if side == "partner" and ctx.place_of_supply in {"customer", "destination"}:
            score += 30
        if ctx.import_export == "import" and side == "company" and reg.role in {"tax", "registration"}:
            score += 20
        if ctx.import_export == "export" and side == "partner" and reg.role in {"tax", "registration"}:
            score += 20
        return score

    def resolve(self, ctx: JurisdictionContext) -> JurisdictionDecision:
        self._validate_context(ctx)
        company_regs = self.db.scalars(
            select(CompanyJurisdiction)
            .where(
                CompanyJurisdiction.company_id == ctx.company_id,
                self._active_clause(ctx.transaction_date, CompanyJurisdiction),
            )
            .with_for_update()
        ).all()
        if not company_regs:
            raise ValueError("No active company jurisdiction is configured for the transaction date")

        partner_regs = []
        if ctx.partner_id is not None:
            partner_regs = self.db.scalars(
                select(PartnerJurisdiction).where(
                    PartnerJurisdiction.partner_id == ctx.partner_id,
                    self._active_clause(ctx.transaction_date, PartnerJurisdiction),
                )
            ).all()

        candidates = [
            (self._candidate_score(reg, side="company", ctx=ctx), reg.jurisdiction_id, "company", reg.id)
            for reg in company_regs
        ]
        candidates += [
            (self._candidate_score(reg, side="partner", ctx=ctx), reg.jurisdiction_id, "partner", reg.id)
            for reg in partner_regs
        ]
        candidates = [c for c in candidates if c[0] > 0]
        if not candidates:
            raise ValueError("No jurisdiction candidate matches the transaction facts")

        max_score = max(c[0] for c in candidates)
        winners = [c for c in candidates if c[0] == max_score]
        winning_jurisdictions = {c[1] for c in winners}
        if len(winning_jurisdictions) != 1:
            raise ValueError("Ambiguous jurisdiction: transaction facts match multiple jurisdictions with equal priority")
        chosen_id = next(iter(winning_jurisdictions))

        jurisdiction = self.db.get(Jurisdiction, chosen_id)
        if jurisdiction is None or not jurisdiction.is_active:
            raise ValueError("Resolved jurisdiction is inactive or missing")

        taxpayer_type = "b2b" if ctx.b2b else "b2c"
        filters = [
            TaxRule.jurisdiction_id == jurisdiction.id,
            self._active_clause(ctx.transaction_date, TaxRule),
            TaxRule.transaction_type.in_([ctx.transaction_type, "all"]),
            TaxRule.taxpayer_type.in_(["both", taxpayer_type]),
        ]
        filters.append(TaxRule.place_of_supply.in_([ctx.place_of_supply, "any"]))
        candidate_rules = self.db.scalars(
            select(TaxRule)
            .where(and_(*filters))
            .order_by(TaxRule.priority.asc(), TaxRule.id.asc())
        ).all()
        rules = [r for r in candidate_rules if self._condition_matches(r, ctx)]
        if not rules:
            raise ValueError("No applicable tax rule matches the complete transaction facts")

        rationale = {
            "company_jurisdictions": [r.jurisdiction_id for r in company_regs],
            "partner_jurisdictions": [r.jurisdiction_id for r in partner_regs],
            "selected_jurisdiction": jurisdiction.code,
            "place_of_supply": ctx.place_of_supply,
            "b2b": ctx.b2b,
            "goods_or_services": ctx.goods_or_services,
            "import_export": ctx.import_export,
            "transaction_type": ctx.transaction_type,
            "transaction_date": ctx.transaction_date.isoformat(),
            "matched_rule_count": len(rules),
            "resolution_score": max_score,
        }
        decision = JurisdictionDecision(
            company_id=ctx.company_id,
            partner_id=ctx.partner_id,
            jurisdiction_id=jurisdiction.id,
            transaction_type=ctx.transaction_type,
            transaction_date=ctx.transaction_date,
            place_of_supply=ctx.place_of_supply,
            b2b=ctx.b2b,
            rationale=rationale,
            rule_ids=[r.id for r in rules],
        )
        self.db.add(decision)
        return decision

    def tax_rules(self, ctx: JurisdictionContext) -> list[TaxRule]:
        decision = self.resolve(ctx)
        return list(
            self.db.scalars(
                select(TaxRule)
                .where(TaxRule.id.in_(decision.rule_ids))
                .order_by(TaxRule.priority.asc(), TaxRule.id.asc())
            ).all()
        )

    @staticmethod
    def calculate_tax(base: Decimal, rate: Decimal) -> Decimal:
        if base < 0 or rate < 0:
            raise ValueError("Tax base and rate cannot be negative")
        return (base * rate / Decimal("100")).quantize(Decimal("0.0001"))


from .snapshot_service import TaxSnapshotService
