from datetime import date
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.modules.accounting.advanced_models import AccountingAutoPostRule,AccountingFXRevaluation,AccountingIntercompanyLink,AccountingElimination,AccountingPostingLink
from app.modules.accounting.journals.models import JournalEntry,JournalEntryLine
from app.modules.accounting.journals.services.journal_service import journal_service
from app.modules.accounting.fiscal_years.repositories.fiscal_year_repository import fiscal_year_repository
from app.modules.companies.models import Company

class AccountingAdvancedService:
    def _scope(self,db,user,company_id):
        if user.tenant_id is None: raise HTTPException(status_code=409,detail="User is not assigned to a tenant")
        if db.scalar(select(Company).where(Company.id==company_id,Company.tenant_id==user.tenant_id,Company.is_active.is_(True))) is None: raise HTTPException(status_code=404,detail="Company not found")
        return user.tenant_id
    def _period(self,db,tenant_id,company_id,when):
        p=fiscal_year_repository.get_period_for_date(db,tenant_id,company_id,when)
        if p is None: raise HTTPException(status_code=409,detail="No open accounting period exists for the posting date")
        return p
    def _post(self,db,tenant,e,user_id):
        if e.journal.requires_approval:
            e=journal_service.submit(db,tenant_id=tenant,entry_id=e.id,user_id=user_id)
            raise HTTPException(status_code=409,detail=f"Journal entry {e.entry_number} requires an independent approval before posting")
        return journal_service.post(db,tenant_id=tenant,entry_id=e.id,user_id=user_id)
    def create_rule(self,db,user,**kw):
        tenant=self._scope(db,user,kw["company_id"]);x=AccountingAutoPostRule(tenant_id=tenant,**kw);db.add(x);db.flush();return x
    def post_source(self,db,user,**kw):
        tenant=self._scope(db,user,kw["company_id"]);p=self._period(db,tenant,kw["company_id"],kw["when"]);source_id=str(kw["source_id"])
        existing=db.scalar(select(AccountingPostingLink).where(AccountingPostingLink.tenant_id==tenant,AccountingPostingLink.company_id==kw["company_id"],AccountingPostingLink.source_module==kw["source_module"],AccountingPostingLink.source_entity==kw["source_entity"],AccountingPostingLink.source_id==source_id))
        if existing:return db.get(JournalEntry,existing.journal_entry_id)
        e=journal_service.create_draft(db,tenant_id=tenant,company_id=kw["company_id"],branch_id=kw["branch_id"],journal_id=kw["journal_id"],fiscal_year_id=p.fiscal_year_id,period_id=p.id,entry_number=f"AUTO-{kw['source_module'][:12]}-{source_id}",entry_date=kw["when"],description=kw["description"],lines=[{"account_combination_id":kw["debit_account_id"],"debit":kw["amount"],"credit":0},{"account_combination_id":kw["credit_account_id"],"debit":0,"credit":kw["amount"]}],user_id=user.id,currency_code=kw["currency_code"],source_module=kw["source_module"],source_entity=kw["source_entity"],source_id=kw["source_id"])
        e=self._post(db,tenant,e,user.id)
        db.add(AccountingPostingLink(tenant_id=tenant,company_id=kw["company_id"],source_module=kw["source_module"],source_entity=kw["source_entity"],source_id=source_id,journal_entry_id=e.id,status="posted"));db.flush();return e
    def post_by_rule(self,db,user,*,company_id,source_module,source_entity,source_id,when,amount,description):
        tenant=self._scope(db,user,company_id)
        rule=db.scalar(select(AccountingAutoPostRule).where(AccountingAutoPostRule.tenant_id==tenant,AccountingAutoPostRule.company_id==company_id,AccountingAutoPostRule.source_module==source_module,AccountingAutoPostRule.source_entity==source_entity,AccountingAutoPostRule.is_active.is_(True)).order_by(AccountingAutoPostRule.id))
        if rule is None: raise HTTPException(status_code=404,detail="No active automatic posting rule exists for this source")
        if not rule.auto_post: raise HTTPException(status_code=409,detail="Automatic posting is disabled for this rule")
        return self.post_source(db,user,company_id=company_id,branch_id=rule.branch_id,journal_id=rule.journal_id,when=when,source_module=source_module,source_entity=source_entity,source_id=source_id,debit_account_id=rule.debit_account_id,credit_account_id=rule.credit_account_id,amount=amount,description=description,currency_code=rule.currency_code)

    def fx_revalue(self,db,user,**kw):
        tenant=self._scope(db,user,kw["company_id"]);p=self._period(db,tenant,kw["company_id"],kw["when"]);old_base=kw["foreign_amount"]*kw["old_rate"];new_base=kw["foreign_amount"]*kw["new_rate"];delta=new_base-old_base
        if delta==0:raise HTTPException(status_code=409,detail="No FX revaluation difference exists")
        amt=abs(delta);debit=kw["foreign_account_id"] if delta<0 else kw["gain_loss_account_id"];credit=kw["gain_loss_account_id"] if delta<0 else kw["foreign_account_id"]
        e=journal_service.create_draft(db,tenant_id=tenant,company_id=kw["company_id"],branch_id=kw["branch_id"],journal_id=kw["journal_id"],fiscal_year_id=p.fiscal_year_id,period_id=p.id,entry_number=f"FX-{kw['when']:%Y%m%d}-{kw['currency_code']}",entry_date=kw["when"],description=f"FX revaluation {kw['currency_code']}",lines=[{"account_combination_id":debit,"debit":amt,"credit":0},{"account_combination_id":credit,"debit":0,"credit":amt}],user_id=user.id,currency_code=kw["currency_code"],source_module="accounting_fx",source_entity="revaluation")
        e=self._post(db,tenant,e,user.id);r=AccountingFXRevaluation(tenant_id=tenant,company_id=kw["company_id"],revaluation_date=kw["when"],currency_code=kw["currency_code"],foreign_amount=kw["foreign_amount"],old_rate=kw["old_rate"],new_rate=kw["new_rate"],old_base_amount=old_base,new_base_amount=new_base,gain_loss=delta,journal_entry_id=e.id,created_by=user.id);db.add(r);db.flush();return r
    def intercompany(self,db,user,**kw):
        tenant=self._scope(db,user,kw["source_company_id"]);self._scope(db,user,kw["target_company_id"])
        if kw["source_company_id"]==kw["target_company_id"]:raise HTTPException(status_code=422,detail="Intercompany requires two different companies")
        ps=self._period(db,tenant,kw["source_company_id"],kw["when"]);pt=self._period(db,tenant,kw["target_company_id"],kw["when"])
        src=journal_service.create_draft(db,tenant_id=tenant,company_id=kw["source_company_id"],branch_id=kw["source_branch_id"],journal_id=kw["source_journal_id"],fiscal_year_id=ps.fiscal_year_id,period_id=ps.id,entry_number=f"IC-S-{kw['reference']}",entry_date=kw["when"],description=kw["description"],lines=[{"account_combination_id":kw["source_debit_account_id"],"debit":kw["amount"],"credit":0},{"account_combination_id":kw["source_credit_account_id"],"debit":0,"credit":kw["amount"]}],user_id=user.id,source_module="intercompany",source_entity="source")
        dst=journal_service.create_draft(db,tenant_id=tenant,company_id=kw["target_company_id"],branch_id=kw["target_branch_id"],journal_id=kw["target_journal_id"],fiscal_year_id=pt.fiscal_year_id,period_id=pt.id,entry_number=f"IC-T-{kw['reference']}",entry_date=kw["when"],description=kw["description"],lines=[{"account_combination_id":kw["target_debit_account_id"],"debit":kw["amount"],"credit":0},{"account_combination_id":kw["target_credit_account_id"],"debit":0,"credit":kw["amount"]}],user_id=user.id,source_module="intercompany",source_entity="target")
        requires_approval = src.journal.requires_approval or dst.journal.requires_approval
        if requires_approval:
            journal_service.submit(db,tenant_id=tenant,entry_id=src.id,user_id=user.id,commit=False)
            journal_service.submit(db,tenant_id=tenant,entry_id=dst.id,user_id=user.id,commit=False)
            link_status = "pending_approval"
        else:
            journal_service.post(db,tenant_id=tenant,entry_id=src.id,user_id=user.id,commit=False)
            journal_service.post(db,tenant_id=tenant,entry_id=dst.id,user_id=user.id,commit=False)
            link_status = "posted"
        x=AccountingIntercompanyLink(tenant_id=tenant,source_company_id=kw["source_company_id"],target_company_id=kw["target_company_id"],source_entry_id=src.id,target_entry_id=dst.id,reference=kw["reference"],status=link_status)
        db.add(x)
        db.commit()
        db.refresh(x)
        return x
    def eliminate(self,db,user,**kw):
        tenant=self._scope(db,user,kw["company_id"]);p=self._period(db,tenant,kw["company_id"],kw["when"])
        e=journal_service.create_draft(db,tenant_id=tenant,company_id=kw["company_id"],branch_id=kw["branch_id"],journal_id=kw["journal_id"],fiscal_year_id=p.fiscal_year_id,period_id=p.id,entry_number=f"ELIM-{kw['consolidation_key']}-{kw['when']:%Y%m%d}",entry_date=kw["when"],description=kw["description"],lines=[{"account_combination_id":kw["debit_account_id"],"debit":kw["amount"],"credit":0},{"account_combination_id":kw["credit_account_id"],"debit":0,"credit":kw["amount"]}],user_id=user.id,source_module="consolidation",source_entity="elimination")
        e=self._post(db,tenant,e,user.id);x=AccountingElimination(tenant_id=tenant,company_id=kw["company_id"],consolidation_key=kw["consolidation_key"],journal_entry_id=e.id,amount=kw["amount"],description=kw["description"]);db.add(x);db.flush();return x
    def reverse_source(self,db,user,*,company_id,source_module,source_entity,source_id,reversal_date=None,reason=None):
        tenant=self._scope(db,user,company_id)
        link=db.scalar(select(AccountingPostingLink).where(AccountingPostingLink.tenant_id==tenant,AccountingPostingLink.company_id==company_id,AccountingPostingLink.source_module==source_module,AccountingPostingLink.source_entity==source_entity,AccountingPostingLink.source_id==str(source_id)).with_for_update())
        if link is None: raise HTTPException(status_code=404,detail="Accounting posting link not found")
        if link.reversal_entry_id is not None: raise HTTPException(status_code=409,detail="Source posting has already been reversed")
        reversal=journal_service.reverse(db,tenant_id=tenant,entry_id=link.journal_entry_id,user_id=user.id,reversal_date=reversal_date,reason=reason)
        link.reversal_entry_id=reversal.id;link.status="reversed";db.flush();return reversal

    def diagnostics(self,db,user,**kw):
        tenant=self._scope(db,user,kw["company_id"]);q=select(JournalEntry).where(JournalEntry.tenant_id==tenant,JournalEntry.company_id==kw["company_id"])
        if kw.get("start_date"):q=q.where(JournalEntry.entry_date>=kw["start_date"])
        if kw.get("end_date"):q=q.where(JournalEntry.entry_date<=kw["end_date"])
        out=[]
        for e in db.scalars(q.order_by(JournalEntry.entry_date.desc(),JournalEntry.id.desc())).all():
            issues=[] 
            if e.status=="posted" and e.total_debit!=e.total_credit:issues.append("posted entry is unbalanced")
            if e.status in {"draft","pending"}:issues.append(f"entry is {e.status}")
            if not e.lines:issues.append("entry has no lines")
            out.append({"entry_id":e.id,"entry_number":e.entry_number,"status":e.status,"source_module":e.source_module,"source_entity":e.source_entity,"source_id":e.source_id,"issues":issues})
        return out
    def drilldown(self,db,user,**kw):
        tenant=self._scope(db,user,kw["company_id"]);q=select(JournalEntryLine,JournalEntry).join(JournalEntry,JournalEntry.id==JournalEntryLine.entry_id).where(JournalEntryLine.tenant_id==tenant,JournalEntryLine.company_id==kw["company_id"],JournalEntryLine.account_combination_id==kw["account_id"],JournalEntry.status=="posted")
        if kw.get("start_date"):q=q.where(JournalEntry.entry_date>=kw["start_date"])
        if kw.get("end_date"):q=q.where(JournalEntry.entry_date<=kw["end_date"])
        return [{"entry_id":e.id,"entry_number":e.entry_number,"date":e.entry_date,"description":e.description,"debit":l.debit,"credit":l.credit,"source_module":e.source_module,"source_entity":e.source_entity,"source_id":e.source_id,"reference":l.reference} for l,e in db.execute(q.order_by(JournalEntry.entry_date,JournalEntry.id,JournalEntryLine.line_number)).all()]
accounting_advanced_service=AccountingAdvancedService()
