from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.modules.identity.models import User
from app.modules.companies.models import Company
from app.modules.branches.models import Branch
from app.modules.products.models import Product
from app.modules.inventory.models import Warehouse,WarehouseLocation
from app.modules.inventory.service import inventory_service
from app.modules.transactions.services.numbering_service import numbering_service
from app.modules.accounting.journals.services.journal_service import journal_service
from app.modules.accounting.journals.schemas.journal import JournalEntryCreate,JournalLineCreate
from .models import Supplier,PurchaseOrder,PurchaseOrderLine,PurchaseReceipt,PurchaseReceiptLine,PurchaseInvoice,PurchaseInvoiceLine
class PurchasingService:
    def tenant(self,u):
        if u.is_platform_admin or u.tenant_id is None: raise HTTPException(403,"An active tenant context is required")
        return u.tenant_id
    def supplier(self,db,t,i):
        x=db.scalar(select(Supplier).where(Supplier.id==i,Supplier.tenant_id==t,Supplier.is_active.is_(True)))
        if not x: raise HTTPException(404,"Supplier not found")
        return x
    def scope(self,db,t,c,b):
        if not db.scalar(select(Company).where(Company.id==c,Company.tenant_id==t)): raise HTTPException(404,"Company not found")
        if not db.scalar(select(Branch).where(Branch.id==b,Branch.company_id==c,Branch.tenant_id==t)): raise HTTPException(404,"Branch not found for company")
    def suppliers(self,db,u): return list(db.scalars(select(Supplier).where(Supplier.tenant_id==self.tenant(u)).order_by(Supplier.name)).all())
    def create_supplier(self,db,p,u):
        t=self.tenant(u); x=Supplier(tenant_id=t,**p.model_dump()); db.add(x)
        try: db.commit()
        except IntegrityError as e: db.rollback(); raise HTTPException(409,"Supplier code already exists") from e
        db.refresh(x); return x
    def create_order(self,db,p,u):
        t=self.tenant(u); self.scope(db,t,p.company_id,p.branch_id); self.supplier(db,t,p.supplier_id)
        lines=[]; sub=disc=tax=Decimal("0")
        for l in p.lines:
            if not db.scalar(select(Product).where(Product.id==l.product_id,Product.tenant_id==t,Product.is_active.is_(True))): raise HTTPException(404,f"Product {l.product_id} not found")
            gross=l.quantity*l.unit_price; d=min(l.discount,gross); taxable=gross-d; tx=(taxable*l.tax_rate/Decimal("100")); total=taxable+tx
            sub+=gross; disc+=d; tax+=tx; lines.append((l,total))
        seq=numbering_service.generate_next_number(db,t,p.company_id,p.branch_id,"PURCHASE_ORDER",commit=False)
        num=seq["generated_number"]
        x=PurchaseOrder(tenant_id=t,order_number=num,subtotal=sub,discount=disc,tax=tax,grand_total=sub-disc+tax,**p.model_dump(exclude={"lines"})); db.add(x); db.flush()
        for l,total in lines: db.add(PurchaseOrderLine(purchase_order_id=x.id,line_total=total,**l.model_dump()))
        db.commit(); db.refresh(x); return x
    def list_orders(self,db,u): return list(db.scalars(select(PurchaseOrder).where(PurchaseOrder.tenant_id==self.tenant(u)).order_by(PurchaseOrder.id.desc())).all())
    def confirm(self,db,i,u):
        t=self.tenant(u); x=db.scalar(select(PurchaseOrder).where(PurchaseOrder.id==i,PurchaseOrder.tenant_id==t))
        if not x: raise HTTPException(404,"Purchase order not found")
        if x.status!="draft": raise HTTPException(409,"Only draft purchase orders can be confirmed")
        x.status="confirmed"; db.commit(); db.refresh(x); return x
    def receive(self,db,p,u):
        t=self.tenant(u); x=db.scalar(select(PurchaseOrder).where(PurchaseOrder.id==p.purchase_order_id,PurchaseOrder.tenant_id==t))
        if not x: raise HTTPException(404,"Purchase order not found")
        if x.status not in ("confirmed","partially_received"): raise HTTPException(409,"Purchase order is not receivable")
        w=db.scalar(select(Warehouse).where(Warehouse.id==p.warehouse_id,Warehouse.tenant_id==t))
        if not w: raise HTTPException(404,"Warehouse not found")
        seq=numbering_service.generate_next_number(db,t,x.company_id,x.branch_id,"PURCHASE_RECEIPT",commit=False); r=PurchaseReceipt(tenant_id=t,purchase_order_id=x.id,warehouse_id=w.id,receipt_number=seq["generated_number"],receipt_date=p.receipt_date,notes=p.notes); db.add(r); db.flush()
        for l in p.lines:
            loc=db.scalar(select(WarehouseLocation).where(WarehouseLocation.id==l.location_id,WarehouseLocation.warehouse_id=w.id,WarehouseLocation.tenant_id==t))
            if not loc: raise HTTPException(404,"Receipt location not found for warehouse")
            db.add(PurchaseReceiptLine(receipt_id=r.id,**l.model_dump()))
            from app.modules.inventory.schemas import MovementCreate
            inventory_service.post_movement(db,t,MovementCreate(warehouse_id=w.id,location_id=loc.id,product_id=l.product_id,movement_type="receipt",quantity=l.quantity,notes=f"Purchase receipt {r.receipt_number}"))
        x.status="received"; db.commit(); db.refresh(r); return r
    def create_invoice(self,db,p,u):
        t=self.tenant(u); x=db.scalar(select(PurchaseOrder).where(PurchaseOrder.id==p.purchase_order_id,PurchaseOrder.tenant_id==t))
        if not x or x.status not in ("confirmed","received"): raise HTTPException(409,"Purchase order is not invoiceable")
        if db.scalar(select(PurchaseInvoice).where(PurchaseInvoice.purchase_order_id==x.id,PurchaseInvoice.tenant_id==t)): raise HTTPException(409,"Purchase invoice already exists")
        seq=numbering_service.generate_next_number(db,t,x.company_id,x.branch_id,"PURCHASE_INVOICE",commit=False)
        inv=PurchaseInvoice(tenant_id=t,company_id=x.company_id,branch_id=x.branch_id,supplier_id=x.supplier_id,purchase_order_id=x.id,invoice_number=seq["generated_number"],invoice_date=p.invoice_date,subtotal=x.subtotal,discount=x.discount,tax=x.tax,grand_total=x.grand_total); db.add(inv); db.flush()
        for l in db.scalars(select(PurchaseOrderLine).where(PurchaseOrderLine.purchase_order_id==x.id)).all(): db.add(PurchaseInvoiceLine(purchase_invoice_id=inv.id,product_id=l.product_id,quantity=l.quantity,unit_price=l.unit_price,discount=l.discount,tax_rate=l.tax_rate,line_total=l.line_total))
        db.commit(); db.refresh(inv); return inv
    def post_invoice(self,db,i,p,u):
        t=self.tenant(u); inv=db.scalar(select(PurchaseInvoice).where(PurchaseInvoice.id==i,PurchaseInvoice.tenant_id==t))
        if not inv: raise HTTPException(404,"Purchase invoice not found")
        if inv.status!="draft": raise HTTPException(409,"Only draft purchase invoices can be posted")
        debit=inv.subtotal-inv.discount; lines=[JournalLineCreate(account_combination_id=p.inventory_account_id,debit=debit,description=f"Purchase {inv.invoice_number}"),JournalLineCreate(account_combination_id=p.payable_account_id,credit=inv.grand_total,description=f"Payable {inv.invoice_number}")]
        if inv.tax:
            if not p.tax_account_id: raise HTTPException(422,"Tax account is required")
            lines[0].debit=debit; lines.insert(1,JournalLineCreate(account_combination_id=p.tax_account_id,debit=inv.tax,description=f"Input tax {inv.invoice_number}"))
        je=journal_service.create_entry(db,JournalEntryCreate(company_id=inv.company_id,branch_id=inv.branch_id,journal_id=p.journal_id,fiscal_year_id=p.fiscal_year_id,period_id=p.period_id,entry_date=inv.invoice_date,description=f"Purchase invoice {inv.invoice_number}",source_module="purchasing",source_entity="purchase_invoice",source_id=inv.id,lines=lines),u)
        inv.journal_entry_id=je.id; inv.status="posted"; db.commit(); db.refresh(inv); return inv
purchasing_service=PurchasingService()