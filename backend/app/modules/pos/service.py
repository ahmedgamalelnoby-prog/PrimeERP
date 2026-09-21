from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import select
from app.modules.identity.models import User
from app.modules.companies.models import Company
from app.modules.branches.models import Branch
from app.modules.inventory.models import Warehouse,WarehouseLocation
from app.modules.products.models import Product
from app.modules.inventory.service import inventory_service
from app.modules.inventory.schemas import IssueCreate,IssueLineCreate
from app.modules.transactions.services.numbering_service import numbering_service
from .models import POSOutlet
from .devices.models import POSTerminal
from .sessions.models import POSSession
from .orders.models import POSOrder,POSOrderLine
from .payments.models import POSPayment
class POSService:
    def tenant(self,u):
        if u.is_platform_admin or u.tenant_id is None: raise HTTPException(403,"An active tenant context is required")
        return u.tenant_id
    def outlet(self,db,t,i):
        x=db.scalar(select(POSOutlet).where(POSOutlet.id==i,POSOutlet.tenant_id==t,POSOutlet.is_active.is_(True)))
        if not x: raise HTTPException(404,"POS outlet not found")
        return x
    def create_outlet(self,db,p,u):
        t=self.tenant(u)
        if not db.scalar(select(Company).where(Company.id==p.company_id,Company.tenant_id==t)): raise HTTPException(404,"Company not found")
        if not db.scalar(select(Branch).where(Branch.id==p.branch_id,Branch.company_id==p.company_id,Branch.tenant_id==t)): raise HTTPException(404,"Branch not found for company")
        if not db.scalar(select(Warehouse).where(Warehouse.id==p.warehouse_id,Warehouse.tenant_id==t)): raise HTTPException(404,"Warehouse not found")
        x=POSOutlet(tenant_id=t,**p.model_dump()); db.add(x); db.commit(); db.refresh(x); return x
    def create_terminal(self,db,p,u):
        t=self.tenant(u); o=self.outlet(db,t,p.outlet_id); x=POSTerminal(tenant_id=t,**p.model_dump()); db.add(x); db.commit(); db.refresh(x); return x
    def open_session(self,db,p,u):
        t=self.tenant(u); term=db.scalar(select(POSTerminal).where(POSTerminal.id==p.terminal_id,POSTerminal.tenant_id==t,POSTerminal.is_active.is_(True)))
        if not term: raise HTTPException(404,"POS terminal not found")
        active=db.scalar(select(POSSession).where(POSSession.terminal_id==term.id,POSSession.tenant_id==t,POSSession.status=="open"))
        if active: raise HTTPException(409,"Terminal already has an open session")
        x=POSSession(tenant_id=t,opened_by=u.id,**p.model_dump()); db.add(x); db.commit(); db.refresh(x); return x
    def create_order(self,db,p,u):
        t=self.tenant(u); o=self.outlet(db,t,p.outlet_id)
        if not db.scalar(select(POSTerminal).where(POSTerminal.id==p.terminal_id,POSTerminal.outlet_id==o.id,POSTerminal.tenant_id==t)): raise HTTPException(404,"Terminal does not belong to outlet")
        s=db.scalar(select(POSSession).where(POSSession.id==p.session_id,POSSession.terminal_id==p.terminal_id,POSSession.tenant_id==t,POSSession.status=="open"))
        if not s: raise HTTPException(409,"POS session is not open")
        seq=numbering_service.generate_next_number(db,t, o.company_id,o.branch_id,"POS_ORDER",commit=False)
        sub=Decimal("0"); x=POSOrder(tenant_id=t,outlet_id=o.id,terminal_id=p.terminal_id,session_id=s.id,order_number=seq["generated_number"]); db.add(x); db.flush()
        for l in p.lines:
            if not db.scalar(select(Product).where(Product.id==l.product_id,Product.tenant_id==t,Product.is_active.is_(True))): raise HTTPException(404,f"Product {l.product_id} not found")
            total=l.quantity*l.unit_price; sub+=total; db.add(POSOrderLine(order_id=x.id,product_id=l.product_id,quantity=l.quantity,unit_price=l.unit_price,line_total=total))
        x.subtotal=sub; x.grand_total=sub; db.commit(); db.refresh(x); return x
    def pay_and_issue(self,db,order_id,p,u):
        t=self.tenant(u); x=db.scalar(select(POSOrder).where(POSOrder.id==order_id,POSOrder.tenant_id==t))
        if not x: raise HTTPException(404,"POS order not found")
        if x.status!="open": raise HTTPException(409,"POS order is not open")
        paid=sum((r.amount for r in db.scalars(select(POSPayment).where(POSPayment.order_id==x.id)).all()),Decimal("0"))
        if paid+p.amount>x.grand_total: raise HTTPException(409,"Payment exceeds order total")
        db.add(POSPayment(tenant_id=t,order_id=x.id,**p.model_dump())); db.flush()
        new_paid=paid+p.amount
        if new_paid==x.grand_total:
            lines=list(db.scalars(select(POSOrderLine).where(POSOrderLine.order_id==x.id)).all())
            loc=db.scalar(select(WarehouseLocation).where(WarehouseLocation.warehouse_id==self.outlet(db,t,x.outlet_id).warehouse_id,WarehouseLocation.tenant_id==t,WarehouseLocation.is_active.is_(True)).order_by(WarehouseLocation.id))
            if not loc: raise HTTPException(409,"Outlet warehouse has no active location")
            issue=inventory_service.issue(db,t,IssueCreate(warehouse_id=loc.warehouse_id,issue_type="pos_sale",reference_type="pos_order",reference_id=x.id,lines=[IssueLineCreate(product_id=l.product_id,location_id=loc.id,quantity=l.quantity) for l in lines]))
            x.status="paid"; db.commit(); db.refresh(x); return x
        db.commit(); db.refresh(x); return x
pos_service=POSService()
