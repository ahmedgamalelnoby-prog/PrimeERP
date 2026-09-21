from datetime import date, datetime, timezone
from decimal import Decimal
from fastapi import HTTPException,status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.modules.identity.models import User
from app.modules.companies.models import Company
from app.modules.branches.models import Branch
from app.modules.accounting.fiscal_years.models import FiscalYear, AccountingPeriod
from app.modules.accounting.chart_of_accounts.models import AccountCombination
from app.modules.accounting.journals.models import AccountingJournal, JournalEntry, JournalEntryLine
from app.modules.transactions.services.numbering_service import numbering_service
from app.modules.accounting.journals.schemas.journal import JournalCreate, JournalUpdate, JournalEntryCreate, JournalEntryUpdate

class JournalService:
    def _tenant(self,user:User)->int:
        if user.is_platform_admin or user.tenant_id is None:
            raise HTTPException(status_code=403,detail="An active tenant context is required")
        return user.tenant_id

    def _company(self,db,tenant_id,company_id):
        c=db.query(Company).filter(Company.id==company_id,Company.tenant_id==tenant_id).first()
        if not c: raise HTTPException(status_code=404,detail="Company not found")
        return c

    def _branch(self,db,tenant_id,company_id,branch_id):
        b=db.query(Branch).filter(Branch.id==branch_id,Branch.company_id==company_id,Branch.tenant_id==tenant_id).first()
        if not b: raise HTTPException(status_code=404,detail="Branch not found for company")
        return b

    def list_journals(self,db,user,company_id=None):
        tenant=self._tenant(user)
        q=db.query(AccountingJournal).filter(AccountingJournal.tenant_id==tenant)
        if company_id:
            self._company(db,tenant,company_id); q=q.filter(AccountingJournal.company_id==company_id)
        return q.order_by(AccountingJournal.code).all()

    def create_journal(self,db,payload,user):
        tenant=self._tenant(user); self._company(db,tenant,payload.company_id)
        obj=AccountingJournal(tenant_id=tenant,created_by=user.id,updated_by=user.id,**payload.model_dump())
        db.add(obj)
        try: db.commit(); db.refresh(obj); return obj
        except IntegrityError as e: db.rollback(); raise HTTPException(status_code=409,detail="Journal code already exists") from e

    def get_journal(self,db,journal_id,user):
        tenant=self._tenant(user)
        obj=db.query(AccountingJournal).filter(AccountingJournal.id==journal_id,AccountingJournal.tenant_id==tenant).first()
        if not obj: raise HTTPException(status_code=404,detail="Journal not found")
        return obj

    def update_journal(self,db,journal_id,payload,user):
        obj=self.get_journal(db,journal_id,user)
        for k,v in payload.model_dump(exclude_unset=True).items(): setattr(obj,k,v)
        obj.updated_by=user.id
        try: db.commit(); db.refresh(obj); return obj
        except IntegrityError as e: db.rollback(); raise HTTPException(status_code=409,detail="Journal code already exists") from e

    def _validate_scope(self,db,tenant,p):
        self._company(db,tenant,p.company_id); self._branch(db,tenant,p.company_id,p.branch_id)
        j=db.query(AccountingJournal).filter(AccountingJournal.id==p.journal_id,AccountingJournal.tenant_id==tenant,AccountingJournal.company_id==p.company_id,AccountingJournal.is_active.is_(True)).first()
        if not j: raise HTTPException(status_code=404,detail="Journal not found for company")
        fy=db.query(FiscalYear).filter(FiscalYear.id==p.fiscal_year_id,FiscalYear.tenant_id==tenant,FiscalYear.company_id==p.company_id).first()
        period=db.query(AccountingPeriod).filter(AccountingPeriod.id==p.period_id,AccountingPeriod.tenant_id==tenant,AccountingPeriod.company_id==p.company_id,AccountingPeriod.fiscal_year_id==p.fiscal_year_id).first()
        if not fy or not period: raise HTTPException(status_code=404,detail="Fiscal year or period not found for company")
        if period.status!="open" or not period.allow_posting: raise HTTPException(status_code=409,detail="Accounting period is not open for posting")
        if not (fy.start_date<=p.entry_date<=fy.end_date and period.start_date<=p.entry_date<=period.end_date): raise HTTPException(status_code=422,detail="Entry date is outside fiscal period")
        return j,period

    def create_entry(self,db,p,user,auto_post=False):
        tenant=self._tenant(user); journal,period=self._validate_scope(db,tenant,p)
        combinations=[]
        for line in p.lines:
            ac=db.query(AccountCombination).filter(AccountCombination.id==line.account_combination_id,AccountCombination.company_id==p.company_id,AccountCombination.is_active.is_(True)).first()
            if not ac: raise HTTPException(status_code=404,detail="Account combination not found for company")
            if line.department_id and line.department_id!=ac.department_id: raise HTTPException(status_code=422,detail="Line department does not match account")
            if line.cost_center_id and line.cost_center_id!=ac.cost_center_id: raise HTTPException(status_code=422,detail="Line cost center does not match account")
            combinations.append(ac)
        tenant_number=numbering_service.generate_next_number(db,tenant,p.company_id,p.branch_id,journal.sequence_key,commit=False)["generated_number"]
        entry=JournalEntry(tenant_id=tenant,created_by=user.id,entry_number=tenant_number,status="draft",total_debit=sum((x.debit for x in p.lines),Decimal("0")),total_credit=sum((x.credit for x in p.lines),Decimal("0")),**p.model_dump(exclude={"lines"}))
        db.add(entry); db.flush()
        for i,(line,ac) in enumerate(zip(p.lines,combinations),1):
            base_debit=line.debit*line.exchange_rate; base_credit=line.credit*line.exchange_rate
            db.add(JournalEntryLine(tenant_id=tenant,entry_id=entry.id,line_number=i,account_combination_id=ac.id,department_id=ac.department_id,cost_center_id=ac.cost_center_id,description=line.description,reference=line.reference,debit=line.debit,credit=line.credit,currency_code=line.currency_code,exchange_rate=line.exchange_rate,base_debit=base_debit,base_credit=base_credit))
        try:
            db.commit()
            if auto_post:
                entry=self.approve(db,entry.id,user)
                entry=self.post(db,entry.id,user)
            else:
                db.refresh(entry)
            return entry
        except IntegrityError as e: db.rollback(); raise HTTPException(status_code=409,detail="Journal entry number or scope conflict") from e

    def get_entry(self,db,entry_id,user):
        tenant=self._tenant(user); obj=db.query(JournalEntry).filter(JournalEntry.id==entry_id,JournalEntry.tenant_id==tenant).first()
        if not obj: raise HTTPException(status_code=404,detail="Journal entry not found")
        return obj

    def list_entries(self,db,user,company_id=None,status_filter=None):
        tenant=self._tenant(user); q=db.query(JournalEntry).filter(JournalEntry.tenant_id==tenant)
        if company_id: q=q.filter(JournalEntry.company_id==company_id)
        if status_filter: q=q.filter(JournalEntry.status==status_filter)
        return q.order_by(JournalEntry.entry_date.desc(),JournalEntry.id.desc()).all()

    def update_entry(self,db,entry_id,payload,user):
        obj=self.get_entry(db,entry_id,user)
        if obj.status!="draft": raise HTTPException(status_code=409,detail="Only draft journal entries can be edited")
        for k,v in payload.model_dump(exclude_unset=True).items(): setattr(obj,k,v)
        db.commit(); db.refresh(obj); return obj

    def _transition(self,db,entry_id,user,expected,new_status,reason=None):
        obj=self.get_entry(db,entry_id,user)
        if obj.status!=expected: raise HTTPException(status_code=409,detail=f"Invalid transition from {obj.status} to {new_status}")
        if new_status=="posted":
            period=db.query(AccountingPeriod).filter(AccountingPeriod.id==obj.period_id,AccountingPeriod.tenant_id==obj.tenant_id).with_for_update().first()
            if not period or period.status!="open" or not period.allow_posting: raise HTTPException(status_code=409,detail="Accounting period is closed or locked")
            obj.posting_date=obj.posting_date or date.today(); obj.posted_by=user.id; obj.posted_at=datetime.now(timezone.utc)
        elif new_status=="pending": obj.submitted_by=user.id; obj.submitted_at=datetime.now(timezone.utc)
        elif new_status=="approved": obj.approved_by=user.id; obj.approved_at=datetime.now(timezone.utc)
        elif new_status=="cancelled": obj.cancelled_by=user.id; obj.cancelled_at=datetime.now(timezone.utc)
        obj.status=new_status
        db.commit(); db.refresh(obj); return obj

    def submit(self,db,i,u): return self._transition(db,i,u,"draft","pending")
    def approve(self,db,i,u): return self._transition(db,i,u,"pending","approved")
    def post(self,db,i,u): return self._transition(db,i,u,"approved","posted")
    def cancel(self,db,i,u): return self._transition(db,i,u,"draft","cancelled")

journal_service=JournalService()
