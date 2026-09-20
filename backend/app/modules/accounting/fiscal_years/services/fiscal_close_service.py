import json
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.modules.accounting.fiscal_years.models import FiscalYear, AccountingPeriod
from app.modules.accounting.fiscal_years.models.close_control import FiscalYearCloseChecklistItem, FiscalYearCloseRun, FiscalYearCloseAudit
from app.modules.accounting.fiscal_years.repositories.fiscal_year_repository import fiscal_year_repository
from app.modules.accounting.journals.models import JournalEntry, JournalEntryLine
from app.modules.accounting.journals.services.journal_service import journal_service
from app.modules.accounting.chart_of_accounts.models import AccountCombination, NaturalAccount
from app.modules.branches.models import Branch
from app.modules.accounting.journals.models import Journal
from app.modules.taxes.models import TaxReturnDraft
from app.modules.audit.service import record_audit_event
from app.modules.companies.models import Company
from app.modules.identity.models import User
from app.modules.treasury.bank_reconciliation.models import BankStatementLine
from app.modules.completion.models import FunctionalTransaction
from app.modules.transactions.models import BusinessTransaction

class FiscalCloseService:
    CHECKS = (
        ("all_normal_periods_closed","All normal accounting periods are closed"),
        ("no_unposted_journals","No draft/pending/approved journal entries remain"),
        ("no_unreconciled_bank","No unreconciled bank statement lines remain"),
        ("no_pending_workflow","No pending functional approvals remain"),
        ("no_open_financial_transactions","No open business transactions remain"),
        ("tax_controls_complete","Tax filing controls for the year are complete"),
    )

    def _scope(self, db, company_id, user):
        if user.tenant_id is None or user.is_platform_admin:
            raise HTTPException(403,"Tenant context is required")
        company=db.scalar(select(Company).where(Company.id==company_id,Company.tenant_id==user.tenant_id))
        if company is None: raise HTTPException(404,"Company not found")
        return company

    def _fy(self, db, fy_id, user):
        fy=db.scalar(select(FiscalYear).where(FiscalYear.id==fy_id,FiscalYear.tenant_id==user.tenant_id).with_for_update())
        if fy is None: raise HTTPException(404,"Fiscal year not found")
        return fy

    def _audit(self, db, fy, user, action, old=None, new=None, reason=None, period_id=None, meta=None):
        db.add(FiscalYearCloseAudit(tenant_id=fy.tenant_id,company_id=fy.company_id,fiscal_year_id=fy.id,period_id=period_id,action=action,from_status=old,to_status=new,reason=reason,actor_id=user.id,metadata_json=json.dumps(meta or {},default=str)))
        record_audit_event(db,action=f"fiscal_year.{action}",entity_type="fiscal_year",entity_id=fy.id,user_id=user.id,tenant_id=fy.tenant_id,company_id=fy.company_id,metadata={"from":old,"to":new,"reason":reason,**(meta or {})})

    def checklist(self, db, company_id, fy_id, user):
        self._scope(db,company_id,user); fy=self._fy(db,fy_id,user)
        if fy.company_id!=company_id: raise HTTPException(403,"Fiscal year is outside company")
        normal=[p for p in fy.periods if not p.is_adjustment]
        counts={}
        counts["all_normal_periods_closed"]=sum(p.status in {"closed","locked"} for p in normal)==len(normal) and bool(normal)
        counts["no_unposted_journals"]=db.scalar(select(func.count(JournalEntry.id)).where(JournalEntry.tenant_id==fy.tenant_id,JournalEntry.company_id==company_id,JournalEntry.fiscal_year_id==fy.id,JournalEntry.status.in_({"draft","pending","approved"})))==0
        BankStatementLine = __import__("app.modules.treasury.bank_reconciliation.models",fromlist=["BankStatementLine"]).BankStatementLine
        counts["no_unreconciled_bank"]=db.scalar(select(func.count()).select_from(BankStatementLine).where(BankStatementLine.company_id==company_id,BankStatementLine.status!="matched"))==0
        counts["no_pending_workflow"]=db.scalar(select(func.count(FunctionalTransaction.id)).where(FunctionalTransaction.tenant_id==fy.tenant_id,FunctionalTransaction.company_id==company_id,FunctionalTransaction.status.in_({"pending","submitted","approved"})))==0
        counts["no_open_financial_transactions"]=db.scalar(select(func.count(BusinessTransaction.id)).where(BusinessTransaction.tenant_id==fy.tenant_id,BusinessTransaction.company_id==company_id,BusinessTransaction.transaction_date>=fy.start_date,BusinessTransaction.transaction_date<=fy.end_date,BusinessTransaction.status.in_({"draft","pending","approved"})))==0
        tax_drafts=db.scalars(select(TaxReturnDraft).where(
            TaxReturnDraft.company_id==company_id,
            TaxReturnDraft.period_from<=fy.end_date,
            TaxReturnDraft.period_to>=fy.start_date,
        )).all()
        counts["tax_controls_complete"]=bool(tax_drafts) and all(
            bool(d.is_reconciled) and d.status in {"reconciled","submitted","accepted","closed"}
            for d in tax_drafts
        )
        items=[]
        for key,name in self.CHECKS:
            ok=bool(counts[key])
            item=db.scalar(select(FiscalYearCloseChecklistItem).where(FiscalYearCloseChecklistItem.tenant_id==fy.tenant_id,FiscalYearCloseChecklistItem.fiscal_year_id==fy.id,FiscalYearCloseChecklistItem.key==key))
            if item is None:
                item=FiscalYearCloseChecklistItem(tenant_id=fy.tenant_id,company_id=company_id,fiscal_year_id=fy.id,key=key,name=name,required=True)
                db.add(item)
            item.status="passed" if ok else "failed"; item.details="passed" if ok else "blocking condition exists"; item.checked_by=user.id; item.checked_at=datetime.now(timezone.utc); items.append(item)
        db.flush()
        return {"fiscal_year_id":fy.id,"status":fy.status,"ready":all(bool(counts[k]) for k,_ in self.CHECKS),"items":[{"key":x.key,"name":x.name,"status":x.status,"details":x.details} for x in items]}

    def close_period(self, db, period_id, user, reason):
        if not reason or not reason.strip(): raise HTTPException(422,"Close reason is required")
        p=db.scalar(select(AccountingPeriod).where(AccountingPeriod.id==period_id,AccountingPeriod.tenant_id==user.tenant_id).with_for_update())
        if p is None: raise HTTPException(404,"Period not found")
        if p.status!="open": raise HTTPException(409,"Only open periods can be closed")
        fy=self._fy(db,p.fiscal_year_id,user); old=p.status;p.status="closed";p.allow_posting=False;p.closed_by=user.id;p.closed_at=datetime.now(timezone.utc)
        self._audit(db,fy,user,"period_close",old,p.status,reason,p.id)
        db.commit();db.refresh(p);return p

    def privileged_reopen(self, db, period_id, user, reason):
        if not user.is_superuser: raise HTTPException(403,"Privileged accounting administrator is required")
        if not reason or not reason.strip(): raise HTTPException(422,"Reopen reason is required")
        p=db.scalar(select(AccountingPeriod).where(AccountingPeriod.id==period_id,AccountingPeriod.tenant_id==user.tenant_id).with_for_update())
        if p is None: raise HTTPException(404,"Period not found")
        fy=self._fy(db,p.fiscal_year_id,user)
        if fy.status=="closed": raise HTTPException(409,"Fiscal year is closed; reopen the fiscal year through the year-end control")
        old=p.status;p.status="open";p.allow_posting=True;p.closed_by=None;p.closed_at=None
        self._audit(db,fy,user,"privileged_period_reopen",old,p.status,reason,p.id,{"privileged":True})
        db.commit();db.refresh(p);return p

    def privileged_reopen_fiscal_year(self, db, fy_id, user, reason):
        if not user.is_superuser: raise HTTPException(403,"Privileged accounting administrator is required")
        if not reason or not reason.strip(): raise HTTPException(422,"Reopen reason is required")
        fy=self._fy(db,fy_id,user)
        if fy.status!="closed": raise HTTPException(409,"Only closed fiscal years can be reopened")
        old=fy.status;fy.status="open";fy.is_current=True;fy.closed_by=None;fy.closed_at=None
        for p in fy.periods:
            if not p.is_adjustment and p.status=="locked":
                p.status="open";p.allow_posting=True;p.closed_by=None;p.closed_at=None
        self._audit(db,fy,user,"privileged_fiscal_year_reopen",old,fy.status,reason,None,{"privileged":True})
        db.commit();db.refresh(fy);return fy

    def year_end_close(self, db, fy_id, user, *, branch_id, journal_id, retained_earnings_account_id, reason):
        if not user.is_superuser: raise HTTPException(403,"Privileged accounting administrator is required")
        if not reason or not reason.strip(): raise HTTPException(422,"Year-end close reason is required")
        fy=self._fy(db,fy_id,user)
        if fy.status!="open": raise HTTPException(409,"Only open fiscal years can be closed")
        check=self.checklist(db,fy.company_id,fy.id,user)
        if not check["ready"]: raise HTTPException(409,{"message":"Year-end checklist is not complete","checklist":check["items"]})
        run=db.scalar(select(FiscalYearCloseRun).where(
            FiscalYearCloseRun.tenant_id==fy.tenant_id,
            FiscalYearCloseRun.company_id==fy.company_id,
            FiscalYearCloseRun.fiscal_year_id==fy.id,
        ).with_for_update())
        if run is not None and run.status=="completed":
            raise HTTPException(409,"Fiscal year close has already been completed")
        branch=db.scalar(select(Branch).where(
            Branch.id==branch_id,
            Branch.company_id==fy.company_id,
            Branch.tenant_id==fy.tenant_id,
            Branch.is_active.is_(True),
        ))
        if branch is None:
            raise HTTPException(422,"Branch does not belong to the selected company and tenant")
        journal=db.scalar(select(Journal).where(
            Journal.id==journal_id,
            Journal.company_id==fy.company_id,
            Journal.tenant_id==fy.tenant_id,
            Journal.is_active.is_(True),
        ))
        if journal is None:
            raise HTTPException(422,"Journal does not belong to the selected company and tenant")
        retained=db.scalar(select(AccountCombination).join(NaturalAccount, NaturalAccount.id==AccountCombination.natural_account_id).where(
            AccountCombination.id==retained_earnings_account_id,
            AccountCombination.company_id==fy.company_id,
            AccountCombination.tenant_id==fy.tenant_id,
            AccountCombination.is_active.is_(True),
            NaturalAccount.financial_statement=="balance_sheet",
            NaturalAccount.account_category.in_({"equity","equity_account","retained_earnings"}),
        ))
        if retained is None:
            raise HTTPException(422,"Retained earnings account must be an active equity account in the selected company")
        period=next((p for p in fy.periods if p.is_adjustment),None)
        if period is None:
            raise HTTPException(409,"Adjustment period is required for year-end closing entries")
        # Reopen adjustment period only for controlled closing run.
        period.status="open";period.allow_posting=True
        rows=db.execute(select(AccountCombination.id,func.coalesce(func.sum(JournalEntryLine.debit-JournalEntryLine.credit),0).label("balance"))
            .join(JournalEntryLine,JournalEntryLine.account_combination_id==AccountCombination.id)
            .join(JournalEntry,JournalEntry.id==JournalEntryLine.entry_id)
            .join(NaturalAccount,NaturalAccount.id==AccountCombination.natural_account_id)
            .where(JournalEntry.tenant_id==fy.tenant_id,JournalEntry.company_id==fy.company_id,JournalEntry.fiscal_year_id==fy.id,JournalEntry.status=="posted",NaturalAccount.financial_statement=="profit_and_loss")
            .group_by(AccountCombination.id)).all()
        lines=[];net=Decimal("0")
        for account_id,balance in rows:
            amount=Decimal(str(balance or 0))
            if amount==0: continue
            if amount>0: lines.append({"account_combination_id":account_id,"debit":0,"credit":amount,"description":"Year-end P&L closing"})
            else: lines.append({"account_combination_id":account_id,"debit":-amount,"credit":0,"description":"Year-end P&L closing"})
            net+=amount
        if not lines: raise HTTPException(409,"No profit-and-loss balances require closing")
        if net>0: lines.append({"account_combination_id":retained_earnings_account_id,"debit":0,"credit":net,"description":"Transfer net profit to retained earnings"})
        elif net<0: lines.append({"account_combination_id":retained_earnings_account_id,"debit":-net,"credit":0,"description":"Transfer net loss to retained earnings"})
        entry=journal_service.create_draft(db,tenant_id=fy.tenant_id,company_id=fy.company_id,branch_id=branch_id,journal_id=journal_id,fiscal_year_id=fy.id,period_id=period.id,entry_number=f"YE-CLOSE-{fy.code}",entry_date=fy.end_date,description=f"Year-end closing {fy.code}",lines=lines,user_id=user.id,source_module="fiscal_year",source_entity="year_end_close",source_id=fy.id,commit=False)
        journal_service.submit(db,tenant_id=fy.tenant_id,entry_id=entry.id,user_id=user.id,commit=False)
        if entry.journal.requires_approval: raise HTTPException(409,"Year-end closing entry requires independent approval before posting")
        journal_service.post(db,tenant_id=fy.tenant_id,entry_id=entry.id,user_id=user.id,commit=False)
        if run is None:
            run=FiscalYearCloseRun(tenant_id=fy.tenant_id,company_id=fy.company_id,fiscal_year_id=fy.id)
            db.add(run)
        run.status="completed";run.reason=reason;run.closing_entry_id=entry.id;run.completed_by=user.id;run.completed_at=datetime.now(timezone.utc)
        old=fy.status;fy.status="closed";fy.is_current=False;fy.closed_by=user.id;fy.closed_at=datetime.now(timezone.utc)
        for p in fy.periods: p.status="locked";p.allow_posting=False
        self._audit(db,fy,user,"year_end_close",old,fy.status,reason,period.id,{"closing_entry_id":entry.id,"retained_earnings_account_id":retained_earnings_account_id})
        db.commit();db.refresh(fy);return {"fiscal_year_id":fy.id,"status":fy.status,"closing_entry_id":entry.id,"net_result":str(net)}

fiscal_close_service=FiscalCloseService()
