from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session
from .models import CompanyJurisdiction, Jurisdiction, JurisdictionDecision, PartnerJurisdiction, TaxRule, TaxSnapshot

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
    def __init__(self, db: Session): self.db = db
    @staticmethod
    def _active_clause(effective_date, cls):
        return and_(cls.effective_from <= effective_date, or_(cls.effective_to.is_(None), cls.effective_to >= effective_date), cls.is_active.is_(True))
    def resolve(self, ctx: JurisdictionContext) -> JurisdictionDecision:
        company_regs = self.db.scalars(select(CompanyJurisdiction).where(CompanyJurisdiction.company_id == ctx.company_id, self._active_clause(ctx.transaction_date, CompanyJurisdiction)).with_for_update()).all()
        if not company_regs: raise ValueError("No active company jurisdiction is configured for the transaction date")
        partner_regs = self.db.scalars(select(PartnerJurisdiction).where(PartnerJurisdiction.partner_id == ctx.partner_id, self._active_clause(ctx.transaction_date, PartnerJurisdiction))).all() if ctx.partner_id is not None else []
        candidates=[]
        for reg in company_regs:
            score=(50 if reg.role=="primary" else 30)+(10 if reg.tax_resident else 0)+(15 if reg.vat_registered else 0)
            if ctx.place_of_supply in {"company","origin","local"}: score+=25
            if ctx.import_export=="import" and reg.role in {"tax","registration"}: score+=20
            candidates.append((score,0,reg.jurisdiction_id))
        for reg in partner_regs:
            score=(10 if reg.tax_resident else 0)+(15 if reg.vat_registered else 0)
            if ctx.place_of_supply in {"customer","destination"}: score+=50
            if ctx.import_export=="export" and reg.role in {"tax","registration"}: score+=20
            candidates.append((score,1,reg.jurisdiction_id))
        _,_,chosen_id=max(candidates,key=lambda x:(x[0],-x[1],-x[2]))
        jurisdiction=self.db.get(Jurisdiction,chosen_id)
        if jurisdiction is None or not jurisdiction.is_active: raise ValueError("Resolved jurisdiction is inactive or missing")
        taxpayer_type="b2b" if ctx.b2b else "b2c"
        filters=[TaxRule.jurisdiction_id==jurisdiction.id,self._active_clause(ctx.transaction_date,TaxRule),TaxRule.transaction_type.in_([ctx.transaction_type,"all"]),TaxRule.taxpayer_type.in_(["both",taxpayer_type])]
        if ctx.place_of_supply: filters.append(TaxRule.place_of_supply.in_([ctx.place_of_supply,"any"]))
        rules=self.db.scalars(select(TaxRule).where(and_(*filters)).order_by(TaxRule.priority.asc(),TaxRule.id.asc())).all()
        decision=JurisdictionDecision(company_id=ctx.company_id,partner_id=ctx.partner_id,jurisdiction_id=jurisdiction.id,transaction_type=ctx.transaction_type,transaction_date=ctx.transaction_date,place_of_supply=ctx.place_of_supply or "company",b2b=ctx.b2b,rationale={"company_jurisdictions":[r.jurisdiction_id for r in company_regs],"partner_jurisdictions":[r.jurisdiction_id for r in partner_regs],"selected_jurisdiction":jurisdiction.code,"place_of_supply":ctx.place_of_supply,"b2b":ctx.b2b,"goods_or_services":ctx.goods_or_services,"import_export":ctx.import_export,"transaction_type":ctx.transaction_type,"transaction_date":ctx.transaction_date.isoformat()},rule_ids=[r.id for r in rules])
        self.db.add(decision); return decision
    @staticmethod
    def calculate_tax(base: Decimal, rate: Decimal) -> Decimal:
        if base<0 or rate<0: raise ValueError("Tax base and rate cannot be negative")
        return (base*rate/Decimal("100")).quantize(Decimal("0.0001"))

class TaxSnapshotService:
    """Captures the exact jurisdiction facts and rule versions used by a document."""
    def __init__(self, db: Session): self.db=db
    def capture(self, *, company_id:int, document_kind:str, document_id:int, context:JurisdictionContext)->TaxSnapshot:
        existing=self.db.scalar(select(TaxSnapshot).where(TaxSnapshot.company_id==company_id,TaxSnapshot.document_kind==document_kind,TaxSnapshot.document_id==document_id).with_for_update())
        if existing: return existing
        decision=JurisdictionEngine(self.db).resolve(context)
        jurisdiction=self.db.get(Jurisdiction,decision.jurisdiction_id)
        rules=self.db.scalars(select(TaxRule).where(TaxRule.id.in_(decision.rule_ids))).all() if decision.rule_ids else []
        snapshot=TaxSnapshot(company_id=company_id,document_kind=document_kind,document_id=document_id,decision_id=decision.id,jurisdiction_code=jurisdiction.code,country_code=jurisdiction.country_code,transaction_date=context.transaction_date,transaction_type=context.transaction_type,place_of_supply=context.place_of_supply or "company",b2b=context.b2b,facts={"company_id":context.company_id,"partner_id":context.partner_id,"goods_or_services":context.goods_or_services,"import_export":context.import_export},rules=[{"id":r.id,"code":r.code,"name":r.name,"tax_type":r.tax_type,"transaction_type":r.transaction_type,"taxpayer_type":r.taxpayer_type,"place_of_supply":r.place_of_supply,"rate":str(r.rate),"priority":r.priority,"conditions":r.conditions or {},"effective_from":r.effective_from.isoformat(),"effective_to":r.effective_to.isoformat() if r.effective_to else None,"source_reference":r.source_reference,"version":r.version} for r in rules])
        self.db.add(snapshot); self.db.flush(); return snapshot
    def get(self,company_id:int,document_kind:str,document_id:int):
        return self.db.scalar(select(TaxSnapshot).where(TaxSnapshot.company_id==company_id,TaxSnapshot.document_kind==document_kind,TaxSnapshot.document_id==document_id))
    @staticmethod
    def calculate_from_snapshot(snapshot:TaxSnapshot,taxable_base:Decimal):
        if taxable_base<0: raise ValueError("Taxable base cannot be negative")
        return [{"rule_id":r["id"],"code":r["code"],"tax_type":r["tax_type"],"rate":Decimal(str(r["rate"])),"amount":JurisdictionEngine.calculate_tax(taxable_base,Decimal(str(r["rate"]))) } for r in snapshot.rules]
