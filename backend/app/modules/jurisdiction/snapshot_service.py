from datetime import date
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Jurisdiction, TaxRule, TaxSnapshot
from .service import JurisdictionContext, JurisdictionEngine


class TaxSnapshotService:
    """Create the one authoritative tax snapshot for a posted business document."""

    def __init__(self, db: Session):
        self.db = db

    def capture(self, document_kind: str, document_id: int, ctx: JurisdictionContext, facts: dict[str, Any] | None = None) -> TaxSnapshot:
        if self.db.scalar(select(TaxSnapshot).where(TaxSnapshot.company_id == ctx.company_id, TaxSnapshot.document_kind == document_kind, TaxSnapshot.document_id == document_id)):
            raise ValueError("Tax snapshot already exists for this document")
        engine = JurisdictionEngine(self.db)
        decision = engine.resolve(ctx)
        jurisdiction = self.db.get(Jurisdiction, decision.jurisdiction_id)
        if jurisdiction is None:
            raise ValueError("Resolved jurisdiction not found")
        rules = list(self.db.scalars(select(TaxRule).where(TaxRule.id.in_(decision.rule_ids)).order_by(TaxRule.priority.asc(), TaxRule.id.asc())).all()) if decision.rule_ids else []
        snapshot = TaxSnapshot(
            company_id=ctx.company_id,
            document_kind=document_kind,
            document_id=document_id,
            decision_id=decision.id,
            jurisdiction_code=jurisdiction.code,
            country_code=jurisdiction.country_code,
            transaction_date=ctx.transaction_date,
            transaction_type=ctx.transaction_type,
            place_of_supply=ctx.place_of_supply or "company",
            b2b=ctx.b2b,
            facts={**(facts or {}), "goods_or_services": ctx.goods_or_services, "import_export": ctx.import_export},
            rules=[{"id": r.id, "code": r.code, "name": r.name, "tax_type": r.tax_type, "rate": str(r.rate), "transaction_type": r.transaction_type, "taxpayer_type": r.taxpayer_type, "place_of_supply": r.place_of_supply, "priority": r.priority, "conditions": r.conditions, "effective_from": r.effective_from.isoformat(), "effective_to": r.effective_to.isoformat() if r.effective_to else None, "version": r.version, "source_reference": r.source_reference} for r in rules],
        )
        self.db.add(snapshot)
        return snapshot

    def get(self, company_id: int, document_kind: str, document_id: int) -> TaxSnapshot | None:
        return self.db.scalar(select(TaxSnapshot).where(TaxSnapshot.company_id == company_id, TaxSnapshot.document_kind == document_kind, TaxSnapshot.document_id == document_id))
