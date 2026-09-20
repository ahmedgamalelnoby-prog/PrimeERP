from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.commerce.models import SalesDocument,PurchaseDocument,SalesLine,PurchaseLine
from app.modules.commerce.backorder_models import CommerceBackorder
class BackorderService:
    def generate_for_document(self,db:Session,*,company_id:int,document_id:int,kind:str):
        model,line_model=(SalesDocument,SalesLine) if kind=="sale" else (PurchaseDocument,PurchaseLine)
        doc=db.scalar(select(model).where(model.id==document_id,model.company_id==company_id).with_for_update())
        if not doc: raise ValueError("Document not found")
        created=[]
        for line in doc.lines:
            remaining=Decimal(line.quantity)-Decimal(line.fulfilled_quantity or 0)
            if remaining<=0: continue
            active=db.scalar(select(CommerceBackorder).where(CommerceBackorder.company_id==company_id,CommerceBackorder.source_kind==kind,CommerceBackorder.source_line_id==line.id,CommerceBackorder.status=="open"))
            if active:
                active.quantity=remaining
                continue
            row=CommerceBackorder(company_id=company_id,source_kind=kind,source_document_id=doc.id,source_line_id=line.id,quantity=remaining)
            db.add(row);created.append(row)
        if created: db.flush()
        return created
    def list_open(self,db,company_id,kind=None):
        q=select(CommerceBackorder).where(CommerceBackorder.company_id==company_id,CommerceBackorder.status=="open")
        if kind:q=q.where(CommerceBackorder.source_kind==kind)
        return list(db.scalars(q.order_by(CommerceBackorder.created_at)).all())
backorder_service=BackorderService()