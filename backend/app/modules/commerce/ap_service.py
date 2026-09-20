import json
from datetime import date,datetime,timezone
from decimal import Decimal
from sqlalchemy import select,func
from fastapi import HTTPException
from app.modules.commerce.models import BusinessPartner,PurchaseDocument,CommercePayment,CommercePaymentAllocation
from app.modules.commerce.ap_models import APWriteOff,APReconciliation,APVarianceWorkflow
from app.modules.commerce.accounting_service import commerce_accounting_service
from app.modules.accounting.fiscal_years.services.fiscal_year_service import fiscal_year_service
from app.modules.companies.models import Company
from app.modules.audit.service import record_audit_event

class APService:
 def _partner(self,db,company_id,pid):
  p=db.scalar(select(BusinessPartner).where(BusinessPartner.id==pid,BusinessPartner.company_id==company_id,BusinessPartner.is_active.is_(True)))
  if not p or p.partner_type not in ("vendor","both"): raise HTTPException(404,"Supplier not found")
  return p
 def _payment(self,db,company_id,payment_id):
  p=db.scalar(select(CommercePayment).where(CommercePayment.id==payment_id,CommercePayment.company_id==company_id).with_for_update())
  if not p or p.document_kind!="purchase" or p.status!="posted": raise HTTPException(404,"Posted supplier payment not found")
  return p
 def _total(self,db,payment_id):
  return Decimal(str(db.scalar(select(func.coalesce(func.sum(CommercePaymentAllocation.amount),0)).where(CommercePaymentAllocation.payment_id==payment_id,CommercePaymentAllocation.status=="active")) or 0))
 def unapplied(self,db,p): return max(Decimal(p.amount)-self._total(db,p.id),Decimal(0))
 def _bill(self,db,company_id,bill_id,partner_id):
  q=[PurchaseDocument.id==bill_id,PurchaseDocument.company_id==company_id,PurchaseDocument.document_type=="bill",PurchaseDocument.status.in_({"confirmed","posted"})]
  if partner_id is not None:q.append(PurchaseDocument.partner_id==partner_id)
  d=db.scalar(select(PurchaseDocument).where(*q).with_for_update())
  if not d: raise HTTPException(404,"Supplier bill not found")
  return d
 def create_advance(self,db,company_id,p,user_id):
  self._partner(db,company_id,p.partner_id);fiscal_year_service.assert_open_for_date(db,company_id=company_id,posting_date=p.payment_date)
  if p.idempotency_key:
   e=db.scalar(select(CommercePayment).where(CommercePayment.company_id==company_id,CommercePayment.idempotency_key==p.idempotency_key).with_for_update())
   if e:return e
  pay=CommercePayment(company_id=company_id,partner_id=p.partner_id,document_id=None,document_kind="purchase",payment_date=p.payment_date,amount=p.amount,wht_amount=0,method=p.method,reference=p.reference,notes=p.notes,idempotency_key=p.idempotency_key,status="posted")
  db.add(pay);db.flush();commerce_accounting_service.post_payment(db,pay,None,user_id)
  return pay
 def allocate(self,db,company_id,payment_id,items,user_id):
  p=self._payment(db,company_id,payment_id);partner=p.partner_id;remaining=self.unapplied(db,p);created=[]
  for i in items:
   amt=Decimal(i.amount)
   if amt>remaining:raise HTTPException(409,"Allocation exceeds unapplied payment")
   d=self._bill(db,company_id,i.document_id,partner);outstanding=Decimal(d.total or 0)-Decimal(d.paid_total or 0)
   if amt>outstanding:raise HTTPException(409,"Allocation exceeds bill outstanding")
   if db.scalar(select(CommercePaymentAllocation).where(CommercePaymentAllocation.company_id==company_id,CommercePaymentAllocation.payment_id==p.id,CommercePaymentAllocation.document_kind=="purchase",CommercePaymentAllocation.document_id==d.id,CommercePaymentAllocation.status=="active")):raise HTTPException(409,"Bill already allocated")
   a=CommercePaymentAllocation(company_id=company_id,payment_id=p.id,document_kind="purchase",document_id=d.id,amount=amt,status="active");db.add(a);d.paid_total=Decimal(d.paid_total or 0)+amt;remaining-=amt;created.append(a)
  db.flush();return {"payment_id":p.id,"allocated":str(Decimal(p.amount)-remaining),"unapplied":str(remaining),"allocations":[{"id":a.id,"document_id":a.document_id,"amount":str(a.amount)} for a in created]}
 def auto_match(self,db,company_id,payment_id,user_id,as_of=None):
  p=self._payment(db,company_id,payment_id);partner=p.partner_id
  if not partner:raise HTTPException(409,"Payment is not linked to a supplier")
  rem=self.unapplied(db,p);matched=[];cutoff=as_of or p.payment_date
  bills=list(db.scalars(select(PurchaseDocument).where(PurchaseDocument.company_id==company_id,PurchaseDocument.partner_id==partner,PurchaseDocument.document_type=="bill",PurchaseDocument.status.in_({"confirmed","posted"}),PurchaseDocument.document_date<=cutoff).order_by(PurchaseDocument.due_date.asc().nulls_last(),PurchaseDocument.document_date.asc(),PurchaseDocument.id.asc()).with_for_update()).all())
  for d in bills:
   if rem<=0:break
   out=Decimal(d.total or 0)-Decimal(d.paid_total or 0)
   if out<=0:continue
   take=min(rem,out);a=CommercePaymentAllocation(company_id=company_id,payment_id=p.id,document_kind="purchase",document_id=d.id,amount=take,status="active");db.add(a);d.paid_total=Decimal(d.paid_total or 0)+take;rem-=take;matched.append({"document_id":d.id,"amount":str(take)})
  db.flush();return {"payment_id":p.id,"matched":matched,"unapplied":str(rem)}
 def request_writeoff(self,db,company_id,payload,user_id):
  d=self._bill(db,company_id,payload.document_id,None);out=Decimal(d.total or 0)-Decimal(d.paid_total or 0)
  if payload.amount>out:raise HTTPException(409,"Write-off exceeds bill outstanding")
  x=APWriteOff(company_id=company_id,partner_id=d.partner_id,document_id=d.id,amount=payload.amount,reason=payload.reason,writeoff_account_id=payload.writeoff_account_id,journal_id=payload.journal_id,status="pending",requested_by=user_id);db.add(x);db.flush();return x
 def create_variance(self,db,company_id,payload,user_id):
  self._bill(db,company_id,payload.bill_id,None);v=Decimal(payload.actual_amount)-Decimal(payload.expected_amount)
  x=APVarianceWorkflow(company_id=company_id,bill_id=payload.bill_id,variance_type=payload.variance_type,expected_amount=payload.expected_amount,actual_amount=payload.actual_amount,variance_amount=v,tolerance=payload.tolerance,status="approved" if abs(v)<=payload.tolerance else "pending",reason=payload.reason,requested_by=user_id)
  db.add(x);db.flush();return x
 def apply_variance_workflow_to_bill(self,db,company_id,bill_id,user_id,tolerance=Decimal("0")):
  result=self.three_way_match(db,company_id,bill_id,user_id,tolerance)
  if result["status"]=="matched": return result
  existing=db.scalar(select(APVarianceWorkflow).where(APVarianceWorkflow.company_id==company_id,APVarianceWorkflow.bill_id==bill_id,APVarianceWorkflow.status=="pending").with_for_update())
  if not existing:
   v=Decimal(result["value_variance"]);q=Decimal(result["quantity_variance"])
   existing=APVarianceWorkflow(company_id=company_id,bill_id=bill_id,variance_type="three_way",expected_amount=Decimal("0"),actual_amount=v,variance_amount=v,tolerance=tolerance,status="pending",reason=f"Quantity variance {q}; value variance {v}",requested_by=user_id);db.add(existing);db.flush()
  return {**result,"variance_workflow_id":existing.id,"workflow_status":existing.status}
 def decide_variance(self,db,company_id,vid,payload,user):
  x=db.scalar(select(APVarianceWorkflow).where(APVarianceWorkflow.id==vid,APVarianceWorkflow.company_id==company_id).with_for_update())
  if not x:raise HTTPException(404,"Variance not found")
  if x.status!="pending":raise HTTPException(409,"Variance already decided")
  x.status="approved" if payload.approve else "rejected";x.decided_by=user.id;x.decided_at=datetime.now(timezone.utc);return x
 def three_way_match(self,db,company_id,bill_id,user_id,tolerance=Decimal("0")):
  bill=self._bill(db,company_id,bill_id,None)
  from app.modules.commerce.models import PurchaseBillReceiptLink,PurchaseBillReceiptAllocation,PurchaseLine
  links=list(db.scalars(select(PurchaseBillReceiptLink).where(PurchaseBillReceiptLink.company_id==company_id,PurchaseBillReceiptLink.bill_id==bill.id)).all())
  receipt_ids=[x.receipt_id for x in links]
  receipts=list(db.scalars(select(PurchaseDocument).where(PurchaseDocument.company_id==company_id,PurchaseDocument.id.in_(receipt_ids or [-1]))).all())
  po_qty=Decimal(0);receipt_qty=Decimal(0);bill_qty=Decimal(0)
  for line in bill.lines: bill_qty+=Decimal(line.quantity or 0)
  for receipt in receipts:
   for line in receipt.lines: receipt_qty+=Decimal(line.quantity or 0)
  if receipt_ids:
   allocations=list(db.scalars(select(PurchaseBillReceiptAllocation).where(PurchaseBillReceiptAllocation.company_id==company_id,PurchaseBillReceiptAllocation.bill_line_id.in_([x.id for x in bill.lines]))).all())
   po_qty=sum((Decimal(a.quantity or 0) for a in allocations),Decimal(0))
  price_expected=sum((Decimal(x.quantity or 0)*Decimal(x.unit_price or 0) for x in bill.lines),Decimal(0))
  qty_variance=bill_qty-receipt_qty; value_variance=Decimal(bill.subtotal or 0)-price_expected
  status="matched" if abs(qty_variance)<=tolerance and abs(value_variance)<=tolerance else "variance"
  return {"bill_id":bill.id,"status":status,"po_receipt_qty":str(po_qty),"receipt_qty":str(receipt_qty),"bill_qty":str(bill_qty),"quantity_variance":str(qty_variance),"value_variance":str(value_variance)}
 def reconcile(self,db,company_id,partner_id,as_of,user_id,persist=True):
  q=[PurchaseDocument.company_id==company_id,PurchaseDocument.document_type=="bill",PurchaseDocument.status.in_({"confirmed","posted"}),PurchaseDocument.document_date<=as_of]
  if partner_id:q.append(PurchaseDocument.partner_id==partner_id)
  bills=list(db.scalars(select(PurchaseDocument).where(*q)).all());ids=[d.id for d in bills]
  als=list(db.scalars(select(CommercePaymentAllocation).where(CommercePaymentAllocation.company_id==company_id,CommercePaymentAllocation.document_kind=="purchase",CommercePaymentAllocation.status=="active",CommercePaymentAllocation.document_id.in_(ids or [-1]))).all());by={}
  for a in als:by[a.document_id]=by.get(a.document_id,Decimal(0))+Decimal(a.amount)
  issues=[];open_bal=Decimal(0)
  for d in bills:
   expected=Decimal(d.total or 0)-by.get(d.id,Decimal(0));actual=Decimal(d.total or 0)-Decimal(d.paid_total or 0)
   open_bal+=max(expected,Decimal(0))
   if abs(expected-actual)>Decimal("0.0001"):issues.append({"type":"paid_total_mismatch","document_id":d.id,"amount":str(expected-actual)})
  details={"bill_open":str(open_bal),"issues":issues};status="balanced" if not issues else "exception"
  if persist:db.add(APReconciliation(company_id=company_id,partner_id=partner_id,as_of=as_of,status=status,discrepancy_amount=sum((Decimal(i["amount"]) for i in issues),Decimal(0)),details_json=json.dumps(details),reconciled_by=user_id))
  return {"status":status,"bill_open":str(open_bal),"issues":issues}
ap_service=APService()
