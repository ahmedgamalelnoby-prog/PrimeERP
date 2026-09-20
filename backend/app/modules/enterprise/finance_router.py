from decimal import Decimal
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.companies.models import Company
from app.modules.enterprise.finance_models import FinanceEntity,ConsolidationGroup,ConsolidationMember,IntercompanyTransaction,ConsolidationRun,ConsolidationLine,ConsolidationElimination,FinanceFxRate,FinanceRevaluation
from app.modules.enterprise.finance_schemas import *
from app.modules.accounting.journals.models.journal_entry import JournalEntry
from app.modules.accounting.journals.models.journal_entry_line import JournalEntryLine
from app.modules.accounting.chart_of_accounts.models import AccountCombination
router=APIRouter(prefix="/enterprise/finance",tags=["Enterprise Finance"])
def company_ok(db,cid,user):
    if not user.tenant_id or not db.scalar(select(Company.id).where(Company.id==cid,Company.tenant_id==user.tenant_id)): raise HTTPException(404,"Company not found")
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
    if not g or not e or g.company_id!=e.company_id:raise HTTPException(404,"Group/entity not found")
    company_ok(db,g.company_id,user);o=ConsolidationMember(group_id=group_id,**p.model_dump());db.add(o);db.commit();db.refresh(o);return {"id":o.id}
@router.post("/intercompany",dependencies=[Depends(require_permission("enterprise.finance.write"))])
def intercompany(p:IntercompanyCreate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    company_ok(db,p.company_id,user)
    if p.from_entity_id==p.to_entity_id:raise HTTPException(422,"Intercompany parties must differ")
    o=IntercompanyTransaction(**p.model_dump());db.add(o);db.commit();db.refresh(o);return {"id":o.id,"status":o.status}
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
    members=list(db.scalars(select(ConsolidationMember).where(ConsolidationMember.group_id==g.id,ConsolidationMember.is_active.is_(True))).all())
    if not members:raise HTTPException(422,"Consolidation group has no active members")
    r=ConsolidationRun(group_id=g.id,period_start=p.period_start,period_end=p.period_end,status="draft",created_by=user.id);db.add(r);db.flush()
    entities=list(db.scalars(select(FinanceEntity).where(FinanceEntity.id.in_([m.entity_id for m in members]))).all());company_ids=[e.company_id for e in entities];pct={e.company_id:Decimal(next(m.consolidation_percent for m in members if m.entity_id==e.id))/Decimal(100) for e in entities}
    rows=db.execute(select(AccountCombination.code,JournalEntryLine.company_id,func.sum(JournalEntryLine.base_debit),func.sum(JournalEntryLine.base_credit)).join(JournalEntry,JournalEntry.id==JournalEntryLine.entry_id).join(AccountCombination,AccountCombination.id==JournalEntryLine.account_combination_id).where(JournalEntryLine.company_id.in_(company_ids),JournalEntry.status=="posted",JournalEntry.entry_date>=p.period_start,JournalEntry.entry_date<=p.period_end).group_by(AccountCombination.code,JournalEntryLine.company_id)).all()
    total_d=Decimal(0);total_c=Decimal(0)
    for code,cid,d,c in rows:
        factor=pct.get(cid,Decimal(1));d=(d or 0)*factor;c=(c or 0)*factor;db.add(ConsolidationLine(run_id=r.id,account_code=code,debit=d,credit=c,source_company_id=cid,ownership_percent=factor*100));total_d+=d;total_c+=c
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
@router.get("/consolidations/{run_id}",dependencies=[Depends(require_permission("enterprise.finance.access"))])
def detail(run_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    r=db.get(ConsolidationRun,run_id)
    if not r:raise HTTPException(404,"Run not found")
    g=db.get(ConsolidationGroup,r.group_id);company_ok(db,g.company_id,user)
    lines=db.scalars(select(ConsolidationLine).where(ConsolidationLine.run_id==run_id)).all();elims=db.scalars(select(ConsolidationElimination).where(ConsolidationElimination.run_id==run_id)).all()
    return {"run":{"id":r.id,"status":r.status,"period_start":r.period_start,"period_end":r.period_end,"total_debit":r.total_debit,"total_credit":r.total_credit,"elimination_total":r.elimination_total},"lines":[{"account_code":x.account_code,"debit":x.debit,"credit":x.credit,"source_company_id":x.source_company_id} for x in lines],"eliminations":[{"account_code":x.account_code,"debit":x.debit,"credit":x.credit,"reason":x.reason} for x in elims]}
