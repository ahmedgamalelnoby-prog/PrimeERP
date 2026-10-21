from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.customers.models import Customer
from app.modules.accounting.journals.schemas.journal import JournalEntryCreate,JournalLineCreate
from app.modules.accounting.journals.services.journal_service import journal_service
from app.modules.transactions.services.numbering_service import numbering_service
from .models import SalesInvoice,SalesInvoiceLine
from app.modules.sales.sales_orders.models import SalesOrder
class InvoiceService:
 def tenant(self,u):
  if u.is_platform_admin or u.tenant_id is None:raise HTTPException(403,"Active tenant context is required")
  return u.tenant_id
 def create_from_order(self,db,u,p):
  t=self.tenant(u);o=db.scalar(select(SalesOrder).where(SalesOrder.id==p.sales_order_id,SalesOrder.tenant_id==t))
  if not o:raise HTTPException(404,"Sales order not found")
  if o.status not in {"fulfilled","confirmed","reserved"}:raise HTTPException(409,"Order is not ready for invoicing")
  existing=db.scalar(select(SalesInvoice).where(SalesInvoice.sales_order_id==o.id,SalesInvoice.tenant_id==t))
  if existing:raise HTTPException(409,"Invoice already exists for this order")
  number=numbering_service.generate_next_number(db,t,o.company_id,o.branch_id,"SALES_INVOICE",commit=False)["generated_number"]
  inv=SalesInvoice(tenant_id=t,company_id=o.company_id,branch_id=o.branch_id,customer_id=o.customer_id,sales_order_id=o.id,invoice_number=number,invoice_date=p.invoice_date,currency_code=p.currency_code.upper(),subtotal=o.subtotal,tax_total=o.tax_total,discount_total=o.discount_total,grand_total=o.grand_total,created_by=u.id)
  db.add(inv);db.flush()
  for l in o.lines:db.add(SalesInvoiceLine(invoice_id=inv.id,product_id=l.product_id,quantity=l.quantity,unit_price=l.unit_price,discount=l.discount,tax_rate=l.tax_rate,line_total=l.line_total))
  db.commit();db.refresh(inv);return inv
 def post(self,db,u,i,p):
  inv=self.get(db,u,i)
  if inv.status!="draft":raise HTTPException(409,"Only draft invoices can be posted")
  if inv.journal_entry_id:raise HTTPException(409,"Invoice already posted")
  lines=[JournalLineCreate(account_combination_id=p.receivable_account_id,debit=inv.grand_total),JournalLineCreate(account_combination_id=p.revenue_account_id,credit=inv.subtotal-inv.discount_total)]
  if inv.tax_total:
   if not p.tax_account_id:raise HTTPException(422,"Tax account is required when invoice has tax")
   lines.append(JournalLineCreate(account_combination_id=p.tax_account_id,credit=inv.tax_total))
  je=journal_service.create_entry(db,JournalEntryCreate(company_id=inv.company_id,branch_id=inv.branch_id,journal_id=p.journal_id,fiscal_year_id=p.fiscal_year_id,period_id=p.period_id,entry_date=inv.invoice_date,posting_date=inv.invoice_date,description=f"Sales invoice {inv.invoice_number}",currency_code=inv.currency_code,lines=lines,source_module="sales",source_entity="sales_invoice",source_id=inv.id),u,auto_post=True)
  inv.journal_entry_id=je.id;inv.status="posted";db.commit();db.refresh(inv);return inv
 def get(self,db,u,i):
  t=self.tenant(u);o=db.scalar(select(SalesInvoice).where(SalesInvoice.id==i,SalesInvoice.tenant_id==t))
  if not o:raise HTTPException(404,"Sales invoice not found")
  return o
 def list(self,db,u):
  t=self.tenant(u);return list(db.scalars(select(SalesInvoice).where(SalesInvoice.tenant_id==t).order_by(SalesInvoice.id.desc())).all())
invoice_service=InvoiceService()