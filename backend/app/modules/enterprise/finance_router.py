from decimal import Decimal
from datetime import date
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.modules.saas.entitlements import require_module
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.companies.models import Company
from app.modules.enterprise.finance_models import FinanceEntity,ConsolidationGroup,ConsolidationMember,IntercompanyTransaction,ConsolidationRun,ConsolidationLine,ConsolidationElimination,FinanceFxRate,FinanceRevaluation
from app.modules.enterprise.finance_schemas import *
from app.modules.accounting.journals.models.journal_entry import JournalEntry
from app.modules.accounting.journals.models.journal_entry_line import JournalEntryLine
from app.modules.accounting.chart_of_accounts.models import AccountCombination
router = APIRouter(
    prefix="/enterprise/finance",
    tags=["Enterprise Finance"],
    dependencies=[Depends(require_module("enterprise"))],
)
def company_ok(db, cid, user):
    tenant_id = get_effective_tenant_id(user)
    if tenant_id is None or not db.scalar(
        select(Company.id).where(
            Company.id == cid,
            Company.tenant_id == tenant_id,
            Company.is_active.is_(True),
        )
    ):
        raise HTTPException(404, "Company not found")
@router.post("/entities",response_model=EntityResponse,status_code=201,dependencies=[Depends(require_permission("enterprise.finance.write"))])
def entity(p:EntityCreate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    company_ok(db,p.company_id,user);o=FinanceEntity(**p.model_dump());db.add(o);db.commit();db.refresh(o);return o
@router.get("/entities",response_model=list[EntityResponse],dependencies=[Depends(require_permission("enterprise.finance.access"))])
def entities(company_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    company_ok(db,company_id,user);return list(db.scalars(select(FinanceEntity).where(FinanceEntity.company_id==company_id)).all())
@router.post("/groups",response_model=GroupResponse,status_code=201,dependencies=[Depends(require_permission("enterprise.finance.write"))])
def group(p:GroupCreate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    company_ok(db,p.company_id,user);o=ConsolidationGroup(**p.model_dump());db.add(o);db.commit();db.refresh(o);return o
@router.post("/groups/{group_id}/members",dependencies=[Depends(require_permission("enterprise.finance.write"))])
def member(group_id:int,p:MemberCreate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    g=db.get(ConsolidationGroup,group_id);e=db.get(FinanceEntity,p.entity_id)
    if not g or not e:raise HTTPException(404,"Group/entity not found")
    company_ok(db,g.company_id,user);company_ok(db,e.company_id,user)
    company_member = db.scalar(
        select(ConsolidationMember.id)
        .join(FinanceEntity, FinanceEntity.id == ConsolidationMember.entity_id)
        .where(
            ConsolidationMember.group_id == group_id,
            ConsolidationMember.is_active.is_(True),
            FinanceEntity.company_id == e.company_id,
        )
    )
    if company_member is not None:
        raise HTTPException(409, "A company can only be represented once in a consolidation group")
    o=ConsolidationMember(group_id=group_id,**p.model_dump());db.add(o);db.commit();db.refresh(o);return {"id":o.id}
@router.post("/intercompany", dependencies=[Depends(require_permission("enterprise.finance.write"))])
def intercompany(p: IntercompanyCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    company_ok(db, p.company_id, user)
    if p.from_entity_id == p.to_entity_id:
        raise HTTPException(422, "Intercompany parties must differ")

    tenant_id = get_effective_tenant_id(user)
    party_ids = {p.from_entity_id, p.to_entity_id}
    tenant_entities = set(db.scalars(
        select(FinanceEntity.id)
        .join(Company, Company.id == FinanceEntity.company_id)
        .where(
            FinanceEntity.id.in_(party_ids),
            FinanceEntity.is_active.is_(True),
            Company.tenant_id == tenant_id,
            Company.is_active.is_(True),
        )
    ).all())
    if tenant_entities != party_ids:
        raise HTTPException(404, "Intercompany entity not found")

    transaction = IntercompanyTransaction(**p.model_dump())
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return {"id": transaction.id, "status": transaction.status}
@router.get("/intercompany",dependencies=[Depends(require_permission("enterprise.finance.access"))])
def intercompanies(company_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    company_ok(db,company_id,user);q=select(IntercompanyTransaction).where(IntercompanyTransaction.company_id==company_id).order_by(IntercompanyTransaction.id.desc())
    return [{"id":x.id,"from_entity_id":x.from_entity_id,"to_entity_id":x.to_entity_id,"reference":x.reference,"amount":x.amount,"status":x.status,"account_code":x.account_code} for x in db.scalars(q).all()]
@router.post("/fx-rates",dependencies=[Depends(require_permission("enterprise.finance.write"))])
def fx(p:FxRateCreate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    company_ok(db,p.company_id,user);o=FinanceFxRate(**p.model_dump());db.add(o);db.commit();db.refresh(o);return {"id":o.id,"rate":o.rate}
@router.post("/revaluations",dependencies=[Depends(require_permission("enterprise.finance.write"))])
def revaluation(p:RevaluationCreate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    company_ok(db,p.company_id,user);gain=(p.base_amount*p.new_rate)-(p.base_amount*p.old_rate);o=FinanceRevaluation(**p.model_dump(),gain_loss=gain);db.add(o);db.commit();db.refresh(o);return {"id":o.id,"gain_loss":o.gain_loss,"status":o.status}
@router.post("/consolidations/run",dependencies=[Depends(require_permission("enterprise.finance.post"))])
def run(p:ConsolidationRunCreate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    g=db.get(ConsolidationGroup,p.group_id)
    if not g:raise HTTPException(404,"Consolidation group not found")
    company_ok(db,g.company_id,user)
    if p.period_end < p.period_start:raise HTTPException(422,"Consolidation period is invalid")
    existing=db.scalar(select(ConsolidationRun).where(ConsolidationRun.group_id==g.id,ConsolidationRun.period_start==p.period_start,ConsolidationRun.period_end==p.period_end))
    if existing:
        return {"run_id":existing.id,"status":existing.status,"duplicate":True,"total_debit":existing.total_debit,"total_credit":existing.total_credit,"elimination_total":existing.elimination_total}
    members=list(db.scalars(select(ConsolidationMember).where(ConsolidationMember.group_id==g.id,ConsolidationMember.is_active.is_(True))).all())
    if not members:raise HTTPException(422,"Consolidation group has no active members")
    member_entity_ids = {member.entity_id for member in members}
    tenant_id = get_effective_tenant_id(user)
    entities = list(db.scalars(
        select(FinanceEntity)
        .join(Company, Company.id == FinanceEntity.company_id)
        .where(
            FinanceEntity.id.in_(member_entity_ids),
            FinanceEntity.is_active.is_(True),
            Company.tenant_id == tenant_id,
            Company.is_active.is_(True),
        )
    ).all())
    if {entity.id for entity in entities} != member_entity_ids:
        raise HTTPException(409, "Consolidation group contains an inactive or out-of-tenant entity")
    entity_by_company = {entity.company_id: entity for entity in entities}
    if len(entity_by_company) != len(entities):
        raise HTTPException(409, "A company can only be represented once in a consolidation group")
    company_ids = list(entity_by_company)
    r=ConsolidationRun(group_id=g.id,period_start=p.period_start,period_end=p.period_end,status="draft",created_by=user.id);db.add(r);db.flush()
    pct={e.company_id:Decimal(next(m.consolidation_percent for m in members if m.entity_id==e.id))/Decimal(100) for e in entities}
    def fx_rate(from_currency:str,to_currency:str):
        if from_currency==to_currency:return Decimal(1)
        for rate_company_id in dict.fromkeys([g.company_id,*company_ids]):
            direct=db.scalar(select(FinanceFxRate.rate).where(FinanceFxRate.company_id==rate_company_id,FinanceFxRate.rate_date==p.period_end,FinanceFxRate.from_currency==from_currency,FinanceFxRate.to_currency==to_currency))
            if direct is not None:return Decimal(direct)
            inverse=db.scalar(select(FinanceFxRate.rate).where(FinanceFxRate.company_id==rate_company_id,FinanceFxRate.rate_date==p.period_end,FinanceFxRate.from_currency==to_currency,FinanceFxRate.to_currency==from_currency))
            if inverse is not None:return Decimal(1)/Decimal(inverse)
        raise HTTPException(422,f"Missing FX rate {from_currency}/{to_currency} for {p.period_end}")
    rows=db.execute(select(AccountCombination.code,JournalEntryLine.company_id,func.sum(JournalEntryLine.base_debit),func.sum(JournalEntryLine.base_credit)).join(JournalEntry,JournalEntry.id==JournalEntryLine.entry_id).join(AccountCombination,AccountCombination.id==JournalEntryLine.account_combination_id).where(JournalEntryLine.company_id.in_(company_ids),JournalEntry.status=="posted",JournalEntry.entry_date>=p.period_start,JournalEntry.entry_date<=p.period_end).group_by(AccountCombination.code,JournalEntryLine.company_id)).all()
    total_d=Decimal(0);total_c=Decimal(0)
    for code,cid,d,c in rows:
        factor=pct.get(cid,Decimal(1));source_currency=entity_by_company[cid].functional_currency;rate=fx_rate(source_currency,g.reporting_currency);d=(d or 0)*factor*rate;c=(c or 0)*factor*rate;db.add(ConsolidationLine(run_id=r.id,account_code=code,debit=d,credit=c,source_company_id=cid,ownership_percent=factor*100));total_d+=d;total_c+=c
    tx=list(db.scalars(select(IntercompanyTransaction).where(IntercompanyTransaction.company_id==g.company_id,IntercompanyTransaction.from_entity_id.in_([m.entity_id for m in members]),IntercompanyTransaction.to_entity_id.in_([m.entity_id for m in members]),IntercompanyTransaction.transaction_date.between(p.period_start,p.period_end),IntercompanyTransaction.status.in_(["open","matched"]))).all())
    elim=Decimal(0)
    for t in tx:
        db.add(ConsolidationElimination(run_id=r.id,intercompany_transaction_id=t.id,account_code=t.account_code,debit=t.amount,credit=t.amount,reason="Automatic intercompany elimination"));t.status="eliminated";elim+=Decimal(t.amount)
    r.total_debit=total_d;r.total_credit=total_c;r.elimination_total=elim;r.status="calculated";db.commit();return {"run_id":r.id,"status":r.status,"total_debit":r.total_debit,"total_credit":r.total_credit,"elimination_total":r.elimination_total}
@router.post("/consolidations/{run_id}/approve",dependencies=[Depends(require_permission("enterprise.finance.post"))])
def approve(run_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    r=db.get(ConsolidationRun,run_id)
    if not r:raise HTTPException(404,"Run not found")
    g=db.get(ConsolidationGroup,r.group_id);company_ok(db,g.company_id,user)
    if r.status!="calculated":raise HTTPException(409,"Only calculated runs can be approved")
    r.status="approved";db.commit();return {"run_id":r.id,"status":r.status}
@router.post("/consolidations/{run_id}/close",dependencies=[Depends(require_permission("enterprise.finance.post"))])
def close(run_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    r=db.get(ConsolidationRun,run_id)
    if not r:raise HTTPException(404,"Run not found")
    g=db.get(ConsolidationGroup,r.group_id);company_ok(db,g.company_id,user)
    if r.status!="approved":raise HTTPException(409,"Only approved runs can be closed")
    r.status="closed";db.commit();return {"run_id":r.id,"status":r.status}
@router.get("/consolidations/{run_id}",dependencies=[Depends(require_permission("enterprise.finance.access"))])
def detail(run_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    r=db.get(ConsolidationRun,run_id)
    if not r:raise HTTPException(404,"Run not found")
    g=db.get(ConsolidationGroup,r.group_id);company_ok(db,g.company_id,user)
    lines=db.scalars(select(ConsolidationLine).where(ConsolidationLine.run_id==run_id)).all();elims=db.scalars(select(ConsolidationElimination).where(ConsolidationElimination.run_id==run_id)).all()
    return {"run":{"id":r.id,"status":r.status,"period_start":r.period_start,"period_end":r.period_end,"total_debit":r.total_debit,"total_credit":r.total_credit,"elimination_total":r.elimination_total},"lines":[{"account_code":x.account_code,"debit":x.debit,"credit":x.credit,"source_company_id":x.source_company_id} for x in lines],"eliminations":[{"account_code":x.account_code,"debit":x.debit,"credit":x.credit,"reason":x.reason} for x in elims]}