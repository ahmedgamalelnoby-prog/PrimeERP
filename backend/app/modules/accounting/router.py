from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.accounting.models import JournalEntry, JournalLine, TaxRate

router=APIRouter(prefix='/accounting',tags=['accounting'])

@router.post('/journal-entries',status_code=201)
def create_entry(payload:dict,db:Session=Depends(get_db)):
    company_id=int(payload.get('company_id',0)); lines=payload.get('lines') or []
    if company_id<=0 or not lines: raise HTTPException(400,'company_id and lines are required')
    debit=sum(Decimal(str(x.get('debit',0))) for x in lines); credit=sum(Decimal(str(x.get('credit',0))) for x in lines)
    if debit<=0 or debit!=credit: raise HTTPException(400,'Journal entry must balance')
    no=str(payload.get('entry_no') or f'JE-{datetime.now(timezone.utc):%Y%m%d%H%M%S%f}')
    if db.scalar(select(JournalEntry).where(JournalEntry.company_id==company_id,JournalEntry.entry_no==no)): raise HTTPException(400,'Entry number already exists')
    e=JournalEntry(company_id=company_id,entry_no=no,entry_date=datetime.now(timezone.utc),source_type=payload.get('source_type'),source_id=payload.get('source_id'),description=payload.get('description'),total_debit=debit,total_credit=credit,status='posted')
    db.add(e);db.flush()
    for x in lines: db.add(JournalLine(journal_entry_id=e.id,account_id=int(x['account_id']),description=x.get('description'),debit=Decimal(str(x.get('debit',0))),credit=Decimal(str(x.get('credit',0)))))
    db.commit();db.refresh(e);return {'id':e.id,'entry_no':e.entry_no,'status':e.status,'total_debit':e.total_debit,'total_credit':e.total_credit}

@router.get('/journal-entries')
def list_entries(company_id:int=Query(...,gt=0),db:Session=Depends(get_db)):
    return list(db.scalars(select(JournalEntry).where(JournalEntry.company_id==company_id).order_by(JournalEntry.entry_date.desc())).all())

@router.post('/tax-rates',status_code=201)
def create_tax(payload:dict,db:Session=Depends(get_db)):
    p=dict(payload); p['rate']=Decimal(str(p.get('rate',0)))
    if p['rate']<0: raise HTTPException(400,'Tax rate cannot be negative')
    o=TaxRate(**p);db.add(o);db.commit();db.refresh(o);return o

@router.get('/tax-rates')
def list_taxes(company_id:int=Query(...,gt=0),db:Session=Depends(get_db)):
    return list(db.scalars(select(TaxRate).where(TaxRate.company_id==company_id,TaxRate.is_active.is_(True)).order_by(TaxRate.code)).all())
