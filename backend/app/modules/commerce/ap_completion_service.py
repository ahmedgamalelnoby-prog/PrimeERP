import json
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import select, func
from fastapi import HTTPException
from app.modules.commerce.models import BusinessPartner, PurchaseDocument, CommercePayment, CommercePaymentAllocation, PurchaseLine, PurchaseBillReceiptLink, PurchaseBillReceiptAllocation
from app.modules.commerce.ap_models import APWriteOff, APVarianceWorkflow
from app.modules.commerce.accounting_service import commerce_accounting_service
from app.modules.accounting.fiscal_years.services.fiscal_year_service import fiscal_year_service
from app.modules.accounting.journals.models import JournalEntry, JournalEntryLine
from app.modules.accounting.journals.services.journal_service import journal_service
from app.modules.accounting.compliance_controls import validate_double_entry, validate_source
from app.modules.companies.models import Company
from app.modules.audit.service import record_audit_event

class APCompletionService:
    def _bill(self,db,company_id,bill_id):
        d=db.scalar(select(PurchaseDocument).where(PurchaseDocument.id==bill_id,PurchaseDocument.company_id==company_id,PurchaseDocument.document_type=="bill",PurchaseDocument.status.in_({"confirmed","posted"})).with_for_update())
        if not d: raise HTTPException(404,"Supplier bill not found")
        return d

    def supplier_aging(self,db,company_id,partner_id,as_of):
        q=[PurchaseDocument.company_id==company_id,PurchaseDocument.document_type=="bill",PurchaseDocument.status.in_({"confirmed","posted"}),PurchaseDocument.document_date<=as_of]
        if partner_id:q.append(PurchaseDocument.partner_id==partner_id)
        rows=[]
        for d in db.scalars(select(PurchaseDocument).where(*q).order_by(PurchaseDocument.due_date.asc().nulls_last(),PurchaseDocument.document_date.asc(),PurchaseDocument.id.asc())).all():
            outstanding=max(Decimal(d.total or 0)-Decimal(d.paid_total or 0),Decimal("0"))
            if outstanding<=0: continue
            due=d.due_date or d.document_date; days=max((as_of-due).days,0)
            bucket="current" if days==0 else "1-30" if days<=30 else "31-60" if days<=60 else "61-90" if days<=90 else "91+"
            rows.append({"document_id":d.id,"document_number":d.number,"partner_id":d.partner_id,"document_date":d.document_date,"due_date":due,"total":str(d.total),"paid_total":str(d.paid_total),"outstanding":str(outstanding),"days_overdue":days,"bucket":bucket})
        return {"as_of":as_of,"rows":rows,"total_outstanding":str(sum((Decimal(r["outstanding"]) for r in rows),Decimal("0")))}

    def supplier_statement(self,db,company_id,partner_id,from_date=None,to_date=None,as_of=None):
        from app.modules.commerce.service import commerce_service
        return commerce_service.partner_statement(db,company_id,partner_id,"vendor",from_date,to_date,as_of)

    def decide_writeoff(self,db,company_id,writeoff_id,approve,reason,user_id):
        x=db.scalar(select(APWriteOff).where(APWriteOff.id==writeoff_id,APWriteOff.company_id==company_id).with_for_update())
        if not x: raise HTTPException(404,"Write-off request not found")
        if x.status!="pending": raise HTTPException(409,"Write-off request is already decided")
        company=db.scalar(select(Company).where(Company.id==company_id))
        if not approve:
            x.status="rejected";x.rejected_by=user_id;x.rejected_at=datetime.now(timezone.utc)
            record_audit_event(db,action="ap.writeoff_rejected",entity_type="ap_writeoff",entity_id=x.id,user_id=user_id,tenant_id=company.tenant_id,company_id=company_id,metadata={"reason":reason})
            return x
        bill=self._bill(db,company_id,x.document_id)
        outstanding=Decimal(bill.total or 0)-Decimal(bill.paid_total or 0)
        if x.amount>outstanding: raise HTTPException(409,"Write-off exceeds current bill outstanding balance")
        fiscal_year_service.assert_open_for_date(db,company_id=company_id,posting_date=date.today())
        settings=commerce_accounting_service._settings(db,company_id)
        _,_,period,fy=commerce_accounting_service._context(db,company_id,date.today())
        validate_double_entry([{"account_combination_id":settings.ap_account_id,"debit":x.amount,"credit":0},{"account_combination_id":x.writeoff_account_id,"debit":0,"credit":x.amount}])
        validate_source(source_module="commerce",source_entity="ap_writeoff",source_id=x.id)
        entry=journal_service.create_draft(db,tenant_id=company.tenant_id,company_id=company_id,branch_id=settings.default_branch_id,journal_id=x.journal_id,fiscal_year_id=fy.id,period_id=period.id,entry_number=f"AP-WO-{x.id}",entry_date=date.today(),description=f"AP write-off {bill.number}",lines=[{"account_combination_id":settings.ap_account_id,"debit":x.amount,"credit":0,"description":f"AP write-off {bill.number}"},{"account_combination_id":x.writeoff_account_id,"debit":0,"credit":x.amount,"description":x.reason}],user_id=user_id,source_module="commerce",source_entity="ap_writeoff",source_id=x.id,commit=False)
        journal_service.submit(db,tenant_id=company.tenant_id,entry_id=entry.id,user_id=user_id,commit=False)
        if entry.journal.requires_approval: raise HTTPException(409,"Write-off journal requires independent approval")
        journal_service.post(db,tenant_id=company.tenant_id,entry_id=entry.id,user_id=user_id,commit=False)
        bill.paid_total=Decimal(bill.paid_total or 0)+x.amount
        x.status="approved";x.approved_by=user_id;x.approved_at=datetime.now(timezone.utc);x.accounting_entry_id=entry.id
        record_audit_event(db,action="ap.writeoff_approved",entity_type="ap_writeoff",entity_id=x.id,user_id=user_id,tenant_id=company.tenant_id,company_id=company_id,metadata={"document_id":bill.id,"amount":str(x.amount),"accounting_entry_id":entry.id})
        return x

    def apply_variance(self,db,company_id,bill_id,user_id,tolerance=Decimal("0")):
        bill=self._bill(db,company_id,bill_id)
        links=list(db.scalars(select(PurchaseBillReceiptLink).where(PurchaseBillReceiptLink.company_id==company_id,PurchaseBillReceiptLink.bill_id==bill.id)).all())
        receipt_ids=[x.receipt_id for x in links]
        receipts=list(db.scalars(select(PurchaseDocument).where(PurchaseDocument.company_id==company_id,PurchaseDocument.id.in_(receipt_ids or [-1]))).all())
        receipt_by_item={}
        for r in receipts:
            for l in r.lines: receipt_by_item[l.item_id]=receipt_by_item.get(l.item_id,Decimal("0"))+Decimal(l.quantity or 0)
        qty_variance=Decimal("0");value_variance=Decimal("0")
        details=[]
        for bl in bill.lines:
            billed=Decimal(bl.quantity or 0)
            received=receipt_by_item.get(bl.item_id,Decimal("0"))
            qv=billed-received; qty_variance+=qv
            expected=received*Decimal(bl.unit_price or 0)
            actual=billed*Decimal(bl.unit_price or 0)
            value_variance+=actual-expected
            if abs(qv)>tolerance: details.append({"bill_line_id":bl.id,"item_id":bl.item_id,"billed_qty":str(billed),"received_qty":str(received),"quantity_variance":str(qv)})
        if abs(qty_variance)<=tolerance and abs(value_variance)<=tolerance:return {"status":"matched","bill_id":bill.id,"quantity_variance":"0","value_variance":"0","details":[]}
        existing=db.scalar(select(APVarianceWorkflow).where(APVarianceWorkflow.company_id==company_id,APVarianceWorkflow.bill_id==bill.id,APVarianceWorkflow.status=="pending").with_for_update())
        if not existing:
            existing=APVarianceWorkflow(company_id=company_id,bill_id=bill.id,variance_type="three_way",expected_amount=Decimal("0"),actual_amount=value_variance,variance_amount=value_variance,tolerance=tolerance,status="pending",reason=json.dumps({"quantity_variance":str(qty_variance),"details":details}),requested_by=user_id)
            db.add(existing);db.flush()
        return {"status":"variance","bill_id":bill.id,"quantity_variance":str(qty_variance),"value_variance":str(value_variance),"details":details,"variance_workflow_id":existing.id,"workflow_status":existing.status}

    def decide_variance(self,db,company_id,variance_id,approve,reason,user_id,waive=False):
        x=db.scalar(select(APVarianceWorkflow).where(APVarianceWorkflow.id==variance_id,APVarianceWorkflow.company_id==company_id).with_for_update())
        if not x: raise HTTPException(404,"Variance not found")
        if x.status!="pending": raise HTTPException(409,"Variance already decided")
        x.status="waived" if waive else ("approved" if approve else "rejected")
        x.decided_by=user_id;x.decided_at=datetime.now(timezone.utc)
        if reason:x.reason=(x.reason or "")+" | "+reason
        company=db.scalar(select(Company).where(Company.id==company_id))
        record_audit_event(db,action="ap.variance_decided",entity_type="ap_variance",entity_id=x.id,user_id=user_id,tenant_id=company.tenant_id,company_id=company_id,metadata={"status":x.status,"reason":reason})
        return x

    def block_bill_posting_if_variance(self,db,company_id,bill_id):
        pending=db.scalar(select(APVarianceWorkflow.id).where(APVarianceWorkflow.company_id==company_id,APVarianceWorkflow.bill_id==bill_id,APVarianceWorkflow.status=="pending"))
        if pending: raise HTTPException(409,"Supplier bill has a pending three-way-match variance approval")

ap_completion_service=APCompletionService()
