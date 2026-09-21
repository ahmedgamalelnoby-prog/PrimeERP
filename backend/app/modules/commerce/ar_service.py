import json
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.modules.commerce.models import BusinessPartner, CommercePayment, CommercePaymentAllocation, SalesDocument
from app.modules.commerce.ar_models import ARWriteOff, ARReconciliation
from app.modules.commerce.ar_schemas import ARAdvanceReceiptRequest
from app.modules.commerce.accounting_service import commerce_accounting_service
from app.modules.accounting.fiscal_years.services.fiscal_year_service import fiscal_year_service
from app.modules.accounting.journals.models import JournalEntry
from app.modules.accounting.journals.services.journal_service import journal_service
from app.modules.accounting.compliance_controls import validate_double_entry, validate_source
from app.modules.companies.models import Company
from app.modules.audit.service import record_audit_event

class ARService:
    def create_advance(self, db, company_id, payload, user_id):
        partner=self._partner(db,company_id,payload.partner_id)
        fiscal_year_service.assert_open_for_date(db,company_id=company_id,posting_date=payload.payment_date)
        if payload.idempotency_key:
            existing=db.scalar(select(CommercePayment).where(CommercePayment.company_id==company_id,CommercePayment.idempotency_key==payload.idempotency_key).with_for_update())
            if existing:
                if existing.document_kind!="sale" or existing.partner_id!=partner.id or Decimal(existing.amount)!=Decimal(payload.amount): raise HTTPException(409,"Idempotency key conflicts with another payment")
                return existing
        payment=CommercePayment(company_id=company_id,partner_id=partner.id,document_id=None,document_kind="sale",payment_date=payload.payment_date,amount=payload.amount,wht_amount=0,method=payload.method,reference=payload.reference,notes=payload.notes,idempotency_key=payload.idempotency_key,status="posted")
        db.add(payment);db.flush()
        commerce_accounting_service.post_payment(db,payment,None,user_id)
        record_audit_event(db,action="ar.advance_created",entity_type="commerce_payment",entity_id=payment.id,user_id=user_id,tenant_id=db.scalar(select(Company.tenant_id).where(Company.id==company_id)),company_id=company_id,metadata={"partner_id":partner.id,"amount":str(payload.amount)})
        return payment

    def _partner(self, db, company_id, partner_id):
        p=db.scalar(select(BusinessPartner).where(BusinessPartner.id==partner_id,BusinessPartner.company_id==company_id,BusinessPartner.is_active.is_(True)))
        if p is None: raise HTTPException(404,"Customer not found")
        if p.partner_type not in ("customer","both"): raise HTTPException(409,"Partner is not a customer")
        return p

    def _payment(self, db, company_id, payment_id):
        p=db.scalar(select(CommercePayment).where(CommercePayment.id==payment_id,CommercePayment.company_id==company_id).with_for_update())
        if p is None or p.document_kind!="sale" or p.status!="posted": raise HTTPException(404,"Posted customer payment not found")
        return p

    def _allocations_total(self, db, payment_id):
        return Decimal(str(db.scalar(select(func.coalesce(func.sum(CommercePaymentAllocation.amount),0)).where(CommercePaymentAllocation.payment_id==payment_id,CommercePaymentAllocation.status=="active")) or 0))

    def unapplied(self, db, payment):
        return max(Decimal(payment.amount)-self._allocations_total(db,payment.id),Decimal("0"))

    def _invoice(self, db, company_id, invoice_id, partner_id):
        d=db.scalar(select(SalesDocument).where(SalesDocument.id==invoice_id,SalesDocument.company_id==company_id,SalesDocument.partner_id==partner_id,SalesDocument.document_type=="invoice",SalesDocument.status.in_({"confirmed","posted"})).with_for_update())
        if d is None: raise HTTPException(404,"Open customer invoice not found")
        return d

    def allocate(self, db, company_id, payment_id, allocations, user_id):
        payment=self._payment(db,company_id,payment_id)
        primary=db.scalar(select(SalesDocument).where(SalesDocument.id==payment.document_id,SalesDocument.company_id==company_id)) if payment.document_id else None
        partner_id=(primary.partner_id if primary else payment.partner_id)
        if partner_id is None: raise HTTPException(409,"Payment is not linked to a customer")
        remaining=Decimal(payment.amount)-self._allocations_total(db,payment.id)
        created=[]
        seen=set()
        for item in allocations:
            if item.document_id in seen: raise HTTPException(422,"Duplicate invoice allocation")
            seen.add(item.document_id); amount=Decimal(item.amount)
            if amount<=0 or amount>remaining: raise HTTPException(409,"Allocation exceeds unapplied payment balance")
            doc=self._invoice(db,company_id,item.document_id,partner_id)
            outstanding=Decimal(doc.total or 0)-Decimal(doc.paid_total or 0)
            if amount>outstanding: raise HTTPException(409,"Allocation exceeds invoice outstanding balance")
            existing=db.scalar(select(CommercePaymentAllocation).where(CommercePaymentAllocation.company_id==company_id,CommercePaymentAllocation.payment_id==payment.id,CommercePaymentAllocation.document_kind=="sale",CommercePaymentAllocation.document_id==doc.id,CommercePaymentAllocation.status=="active").with_for_update())
            if existing: raise HTTPException(409,"Invoice is already allocated by this payment")
            a=CommercePaymentAllocation(company_id=company_id,payment_id=payment.id,document_kind="sale",document_id=doc.id,amount=amount,status="active")
            db.add(a); doc.paid_total=Decimal(doc.paid_total or 0)+amount; remaining-=amount; created.append(a)
        db.flush()
        record_audit_event(db,action="ar.payment_allocated",entity_type="commerce_payment",entity_id=payment.id,user_id=user_id,tenant_id=db.scalar(select(Company.tenant_id).where(Company.id==company_id)),company_id=company_id,metadata={"allocated":str(sum((Decimal(x.amount) for x in created),Decimal(0))),"unapplied":str(remaining)})
        return {"payment_id":payment.id,"allocated":str(Decimal(payment.amount)-remaining),"unapplied":str(remaining),"allocations":[{"id":x.id,"document_id":x.document_id,"amount":str(x.amount)} for x in created]}

    def auto_match(self, db, company_id, payment_id, user_id, as_of=None):
        payment=self._payment(db,company_id,payment_id)
        primary=db.scalar(select(SalesDocument).where(SalesDocument.id==payment.document_id,SalesDocument.company_id==company_id)) if payment.document_id else None
        if primary is None: raise HTTPException(409,"Payment must identify the customer for auto-match")
        partner_id=(primary.partner_id if primary else payment.partner_id)
        if partner_id is None: raise HTTPException(409,"Payment is not linked to a customer")
        remaining=self.unapplied(db,payment)
        if remaining<=0: return {"payment_id":payment.id,"matched":[],"unapplied":"0"}
        cutoff=as_of or payment.payment_date
        invoices=list(db.scalars(select(SalesDocument).where(SalesDocument.company_id==company_id,SalesDocument.partner_id==partner_id,SalesDocument.document_type=="invoice",SalesDocument.status.in_({"confirmed","posted"}),SalesDocument.document_date<=cutoff).order_by(SalesDocument.due_date.asc().nulls_last(),SalesDocument.document_date.asc(),SalesDocument.id.asc()).with_for_update()).all())
        matched=[]
        for doc in invoices:
            if remaining<=0: break
            outstanding=Decimal(doc.total or 0)-Decimal(doc.paid_total or 0)
            if outstanding<=0: continue
            take=min(remaining,outstanding)
            existing=db.scalar(select(CommercePaymentAllocation).where(CommercePaymentAllocation.company_id==company_id,CommercePaymentAllocation.payment_id==payment.id,CommercePaymentAllocation.document_kind=="sale",CommercePaymentAllocation.document_id==doc.id,CommercePaymentAllocation.status=="active").with_for_update())
            if existing: continue
            a=CommercePaymentAllocation(company_id=company_id,payment_id=payment.id,document_kind="sale",document_id=doc.id,amount=take,status="active")
            db.add(a); doc.paid_total=Decimal(doc.paid_total or 0)+take; remaining-=take; matched.append({"document_id":doc.id,"amount":str(take)})
        db.flush()
        record_audit_event(db,action="ar.payment_auto_matched",entity_type="commerce_payment",entity_id=payment.id,user_id=user_id,tenant_id=db.scalar(select(Company.tenant_id).where(Company.id==company_id)),company_id=company_id,metadata={"matched":matched,"unapplied":str(remaining)})
        return {"payment_id":payment.id,"matched":matched,"unapplied":str(remaining)}

    def request_writeoff(self, db, company_id, payload, user_id):
        doc=self._invoice(db,company_id,payload.document_id,None if False else db.scalar(select(SalesDocument.partner_id).where(SalesDocument.id==payload.document_id,SalesDocument.company_id==company_id)))
        outstanding=Decimal(doc.total or 0)-Decimal(doc.paid_total or 0)
        if payload.amount>outstanding: raise HTTPException(409,"Write-off exceeds invoice outstanding balance")
        obj=ARWriteOff(company_id=company_id,partner_id=doc.partner_id,document_id=doc.id,amount=payload.amount,reason=payload.reason,writeoff_account_id=payload.writeoff_account_id,journal_id=payload.journal_id,status="pending",requested_by=user_id)
        db.add(obj); db.flush(); return obj

    def decide_writeoff(self, db, company_id, writeoff_id, payload, user):
        obj=db.scalar(select(ARWriteOff).where(ARWriteOff.id==writeoff_id,ARWriteOff.company_id==company_id).with_for_update())
        if obj is None: raise HTTPException(404,"Write-off request not found")
        if obj.status!="pending": raise HTTPException(409,"Write-off request is already decided")
        if not payload.approve:
            obj.status="rejected";obj.rejected_by=user.id;obj.rejected_at=datetime.now(timezone.utc);db.flush();return obj
        fiscal_year_service.assert_open_for_date(db,company_id=company_id,posting_date=date.today())
        settings=commerce_accounting_service._settings(db,company_id)
        doc=db.scalar(select(SalesDocument).where(SalesDocument.id==obj.document_id,SalesDocument.company_id==company_id).with_for_update())
        if doc is None: raise HTTPException(404,"Invoice not found")
        outstanding=Decimal(doc.total or 0)-Decimal(doc.paid_total or 0)
        if obj.amount>outstanding: raise HTTPException(409,"Write-off exceeds current invoice outstanding balance")
        company=db.scalar(select(Company).where(Company.id==company_id));
        period=commerce_accounting_service._context(db,company_id,date.today())[2]; fy=commerce_accounting_service._context(db,company_id,date.today())[3]
        validate_double_entry([{"account_combination_id":obj.writeoff_account_id,"debit":obj.amount,"credit":0},{"account_combination_id":settings.ar_account_id,"debit":0,"credit":obj.amount}])
        validate_source(source_module="commerce",source_entity="ar_writeoff",source_id=obj.id)
        entry=journal_service.create_draft(db,tenant_id=company.tenant_id,company_id=company_id,branch_id=settings.default_branch_id,journal_id=obj.journal_id,fiscal_year_id=fy.id,period_id=period.id,entry_number=f"AR-WO-{obj.id}",entry_date=date.today(),description=f"AR write-off {doc.number}",lines=[{"account_combination_id":obj.writeoff_account_id,"debit":obj.amount,"credit":0,"description":obj.reason},{"account_combination_id":settings.ar_account_id,"debit":0,"credit":obj.amount,"description":f"AR write-off {doc.number}"}],user_id=user.id,source_module="commerce",source_entity="ar_writeoff",source_id=obj.id,commit=False)
        journal_service.submit(db,tenant_id=company.tenant_id,entry_id=entry.id,user_id=user.id,commit=False)
        if entry.journal.requires_approval: raise HTTPException(409,"Write-off journal requires independent approval")
        journal_service.post(db,tenant_id=company.tenant_id,entry_id=entry.id,user_id=user.id,commit=False)
        doc.paid_total=Decimal(doc.paid_total or 0)+obj.amount
        obj.status="approved";obj.approved_by=user.id;obj.approved_at=datetime.now(timezone.utc);obj.accounting_entry_id=entry.id;db.flush();return obj

    def reconcile(self, db, company_id, partner_id, as_of, user_id, persist=True):
        q=[SalesDocument.company_id==company_id,SalesDocument.document_type=="invoice",SalesDocument.status.in_({"confirmed","posted"}),SalesDocument.document_date<=as_of]
        if partner_id: q.append(SalesDocument.partner_id==partner_id)
        invoices=list(db.scalars(select(SalesDocument).where(*q)).all())
        ids=[x.id for x in invoices]
        allocations=list(db.scalars(select(CommercePaymentAllocation).where(CommercePaymentAllocation.company_id==company_id,CommercePaymentAllocation.document_kind=="sale",CommercePaymentAllocation.status=="active",CommercePaymentAllocation.document_id.in_(ids or [-1]))).all())
        by_doc={}
        for a in allocations: by_doc[a.document_id]=by_doc.get(a.document_id,Decimal(0))+Decimal(a.amount)
        issues=[]; invoice_open=Decimal(0)
        for d in invoices:
            expected=Decimal(d.total or 0)-by_doc.get(d.id,Decimal(0))
            if expected<0: issues.append({"type":"over_allocated_invoice","document_id":d.id,"amount":str(-expected)})
            if abs(expected-(Decimal(d.total or 0)-Decimal(d.paid_total or 0)))>Decimal("0.0001"): issues.append({"type":"paid_total_mismatch","document_id":d.id,"amount":str(expected-(Decimal(d.total or 0)-Decimal(d.paid_total or 0)))})
            invoice_open+=max(expected,Decimal(0))
        pquery=[CommercePayment.company_id==company_id,CommercePayment.document_kind=="sale",CommercePayment.status=="posted",CommercePayment.payment_date<=as_of]
        if partner_id and ids: pquery.append(CommercePayment.document_id.in_(ids))
        payments=list(db.scalars(select(CommercePayment).where(*pquery)).all())
        unapplied=sum((self.unapplied(db,p) for p in payments),Decimal(0))
        gl_balance=None
        gl_difference=Decimal("0")
        if partner_id is None:
            from app.modules.accounting.journals.models import JournalEntry, JournalEntryLine
            from app.modules.commerce.accounting_models import CommerceAccountingSettings
            settings=db.scalar(select(CommerceAccountingSettings).where(CommerceAccountingSettings.company_id==company_id))
            if settings is not None:
                gl_balance=Decimal(str(db.scalar(select(func.coalesce(func.sum(JournalEntryLine.debit-JournalEntryLine.credit),0)).join(JournalEntry,JournalEntry.id==JournalEntryLine.entry_id).where(JournalEntry.company_id==company_id,JournalEntry.status=="posted",JournalEntry.entry_date<=as_of,JournalEntryLine.account_combination_id==settings.ar_account_id)) or 0))
                credit_notes=Decimal(str(db.scalar(select(func.coalesce(func.sum(SalesDocument.total),0)).where(SalesDocument.company_id==company_id,SalesDocument.document_type=="credit_note",SalesDocument.status.in_({"confirmed","posted"}),SalesDocument.document_date<=as_of)) or 0))
                subledger_balance=sum((Decimal(d.total or 0) for d in invoices),Decimal(0))-credit_notes-sum((by_doc.get(d.id,Decimal(0)) for d in invoices),Decimal(0))-sum((Decimal(w.amount or 0) for w in db.scalars(select(ARWriteOff).where(ARWriteOff.company_id==company_id,ARWriteOff.status=="approved",ARWriteOff.created_at<=as_of)).all()),Decimal(0))
                gl_difference=gl_balance-subledger_balance
                if abs(gl_difference)>Decimal("0.01"): issues.append({"type":"gl_subledger_mismatch","amount":str(gl_difference)})
        details={"invoice_open":str(invoice_open),"unapplied_payments":str(unapplied),"gl_balance":str(gl_balance) if gl_balance is not None else None,"gl_difference":str(gl_difference),"issues":issues}
        status="balanced" if not issues else "exception"
        if persist:
            row=ARReconciliation(company_id=company_id,partner_id=partner_id,as_of=as_of,status=status,discrepancy_amount=sum((Decimal(x.get("amount","0")) for x in issues),Decimal(0)),details_json=json.dumps(details,default=str),reconciled_by=user_id);db.add(row);db.flush()
        return {"status":status,"invoice_open":str(invoice_open),"unapplied_payments":str(unapplied),"issues":issues}

ar_service=ARService()
