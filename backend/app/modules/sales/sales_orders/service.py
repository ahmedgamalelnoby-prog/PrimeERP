from decimal import Decimal,ROUND_HALF_UP
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.modules.companies.models import Company
from app.modules.branches.models import Branch
from app.modules.customers.models import Customer
from app.modules.products.models import Product
from app.modules.transactions.services.numbering_service import numbering_service
from .models import SalesOrder,SalesOrderLine
class SalesOrderService:
 def tenant(self,u):
  if u.is_platform_admin or u.tenant_id is None: raise HTTPException(403,"Active tenant context is required")
  return u.tenant_id
 def scope(self,db,t,p):
  if not db.scalar(select(Company).where(Company.id==p.company_id,Company.tenant_id==t)):raise HTTPException(404,"Company not found")
  if not db.scalar(select(Branch).where(Branch.id==p.branch_id,Branch.company_id==p.company_id,Branch.tenant_id==t)):raise HTTPException(404,"Branch not found for company")
  if not db.scalar(select(Customer).where(Customer.id==p.customer_id,Customer.tenant_id==t,Customer.is_active.is_(True))):raise HTTPException(404,"Customer not found")
 def create(self,db,p,u):
  t=self.tenant(u);self.scope(db,t,p);rows=[];subtotal=tax=discount=Decimal("0")
  for x in p.lines:
   product=db.scalar(select(Product).where(Product.id==x.product_id,Product.tenant_id==t,Product.is_active.is_(True)))
   if not product:raise HTTPException(404,f"Product {x.product_id} not found")
   gross=(x.quantity*x.unit_price).quantize(Decimal("0.01"),rounding=ROUND_HALF_UP);disc=x.discount.quantize(Decimal("0.01"),rounding=ROUND_HALF_UP)
   if disc>gross:raise HTTPException(422,"Line discount cannot exceed gross amount")
   net=gross-disc;tax_amt=(net*x.tax_rate/Decimal("100")).quantize(Decimal("0.01"),rounding=ROUND_HALF_UP);rows.append((x,disc,tax_amt,net+tax_amt));subtotal+=gross;discount+=disc;tax+=tax_amt
  try:number=numbering_service.generate_next_number(db,t,p.company_id,p.branch_id,"SALES_ORDER",commit=False)["generated_number"]
  except HTTPException:raise HTTPException(409,"SALES_ORDER numbering sequence is not configured")
  o=SalesOrder(tenant_id=t,created_by=u.id,order_number=number,company_id=p.company_id,branch_id=p.branch_id,customer_id=p.customer_id,order_date=p.order_date,currency_code=p.currency_code.upper(),subtotal=subtotal,tax_total=tax,discount_total=discount,grand_total=subtotal-discount+tax,notes=p.notes);db.add(o);db.flush()
  for x,disc,tax_amt,total in rows:db.add(SalesOrderLine(order_id=o.id,product_id=x.product_id,quantity=x.quantity,unit_price=x.unit_price,discount=disc,tax_rate=x.tax_rate,line_total=total))
  try:db.commit();db.refresh(o);return o
  except IntegrityError as e:db.rollback();raise HTTPException(409,"Sales order conflict") from e
 def list(self,db,u,status_filter=None):
  t=self.tenant(u);q=select(SalesOrder).where(SalesOrder.tenant_id==t)
  if status_filter:q=q.where(SalesOrder.status==status_filter)
  return list(db.scalars(q.order_by(SalesOrder.id.desc())).unique().all())
 def get(self,db,u,i):
  t=self.tenant(u);o=db.scalar(select(SalesOrder).where(SalesOrder.id==i,SalesOrder.tenant_id==t))
  if not o:raise HTTPException(404,"Sales order not found")
  return o
 def transition(self,db,u,i,expected,new):
  o=self.get(db,u,i)
  if o.status!=expected:raise HTTPException(409,f"Invalid transition from {o.status}")
  o.status=new;db.commit();db.refresh(o);return o
sales_order_service=SalesOrderService()