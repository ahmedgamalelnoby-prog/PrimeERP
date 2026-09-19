from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.commerce.models import BusinessPartner
from app.modules.commerce.schemas import DocumentCreate, DocumentLineCreate, PaymentCreate
from app.modules.commerce.service import commerce_service
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models.user import User

router=APIRouter(prefix="/pos",tags=["POS"])

class CheckoutLine(BaseModel):
    item_id:int=Field(gt=0); variant_id:int|None=None; quantity:Decimal=Field(gt=0); unit_price:Decimal=Field(ge=0); discount_percent:Decimal=Field(default=0,ge=0,le=100)
class Checkout(BaseModel):
    company_id:int=Field(gt=0); partner_id:int=Field(gt=0); warehouse_id:int=Field(gt=0); number:str=Field(min_length=1,max_length=60)
    payment_date:__import__("datetime").date; method:str=Field(min_length=1,max_length=30); lines:list[CheckoutLine]=Field(min_length=1)

def _company(db,cid,user):
    if user.tenant_id is None: raise HTTPException(403,"User is not assigned to a tenant")
    if db.scalar(select(Company).where(Company.id==cid,Company.tenant_id==user.tenant_id,Company.is_active.is_(True))) is None: raise HTTPException(403,"Company is outside the current tenant")

@router.get("/sales")
def sales(company_id:int=Query(...,gt=0),current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    _company(db,company_id,current_user); return commerce_service.list_documents(db,company_id,"sale","invoice")

@router.post("/checkout")
def checkout(payload:Checkout,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    _company(db,payload.company_id,current_user)
    lines=[DocumentLineCreate(item_id=x.item_id,variant_id=x.variant_id,quantity=x.quantity,unit_price=x.unit_price,discount_percent=x.discount_percent) for x in payload.lines]
    doc=commerce_service.create_document(db,DocumentCreate(company_id=payload.company_id,partner_id=payload.partner_id,document_type="invoice",number=payload.number,document_date=payload.payment_date,warehouse_id=payload.warehouse_id,lines=lines))
    snapshot=capture_document_tax_snapshot(db,doc,kind="sale")
    if snapshot is None: raise HTTPException(422,"A jurisdiction tax snapshot is required before posting this POS invoice")
    validate_document_tax_snapshot(doc,snapshot)
    commerce_service.confirm(db,payload.company_id,doc.id,"sale",current_user.id)
    commerce_service.post_inventory(db,payload.company_id,doc.id,"sale",user_id=current_user.id)
    commerce_service.pay(db,PaymentCreate(company_id=payload.company_id,document_id=doc.id,payment_date=payload.payment_date,amount=doc.total,method=payload.method), "sale", current_user.id)
    db.commit(); db.refresh(doc); return doc
