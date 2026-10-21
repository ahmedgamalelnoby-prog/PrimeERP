from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.commerce.models import BusinessPartner
from app.modules.commerce.schemas import PartnerCreate, DocumentCreate
from app.modules.commerce.service import commerce_service
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models.user import User
from app.modules.saas.entitlements import require_module

router = APIRouter(
    prefix="/crm",
    tags=["CRM"],
    dependencies=[Depends(require_permission("commerce.access")), Depends(require_module("crm"))],
)

def _company(db, company_id, user):
    tenant_id = get_effective_tenant_id(user)
    if tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(
        select(Company).where(
            Company.id == company_id,
            Company.tenant_id == tenant_id,
            Company.is_active.is_(True),
        )
    )
    if company is None:
        raise HTTPException(403, "Company is outside the current tenant")
    return company

class LeadCreate(BaseModel):
    company_id:int=Field(gt=0); code:str=Field(min_length=1,max_length=50); name:str=Field(min_length=1,max_length=200)
    phone:str|None=None; email:str|None=None; notes:str|None=None

class OpportunityCreate(DocumentCreate):
    pass

@router.get("/dashboard")
def dashboard(company_id:int=Query(...,gt=0), current_user:User=Depends(get_current_user), db:Session=Depends(get_db)):
    _company(db,company_id,current_user)
    leads=list(db.scalars(select(BusinessPartner).where(BusinessPartner.company_id==company_id,BusinessPartner.partner_type.in_(["customer","both"]),BusinessPartner.is_active.is_(True)).order_by(BusinessPartner.id.desc()).limit(200)).all())
    opportunities=commerce_service.list_documents(db,company_id,"sale","quotation")
    return {"leads":[{"id":x.id,"code":x.code,"name":x.name,"phone":x.phone,"email":x.email} for x in leads],"opportunities":[x for x in opportunities]}

@router.post("/leads", status_code=201, dependencies=[Depends(require_permission("commerce.write"))])
def create_lead(payload:LeadCreate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    _company(db,payload.company_id,current_user)
    if db.scalar(select(BusinessPartner).where(BusinessPartner.company_id==payload.company_id,BusinessPartner.code==payload.code)): raise HTTPException(409,"Lead code already exists")
    obj=commerce_service.create_partner(db,PartnerCreate(company_id=payload.company_id,code=payload.code,name=payload.name,partner_type="customer",phone=payload.phone,email=payload.email))
    db.commit(); db.refresh(obj)
    return obj

@router.post("/opportunities", status_code=201, dependencies=[Depends(require_permission("commerce.write"))])
def create_opportunity(payload:OpportunityCreate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    _company(db,payload.company_id,current_user)
    if payload.document_type!="quotation": raise HTTPException(422,"CRM opportunities must start as quotations")
    obj=commerce_service.create_document(db,payload); db.commit(); db.refresh(obj); return obj

@router.post("/opportunities/{document_id}/advance", dependencies=[Depends(require_permission("commerce.write"))])
def advance_opportunity(document_id:int,company_id:int=Query(...,gt=0),target:str=Query(...,pattern="^(order|invoice)$"),current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    _company(db,company_id,current_user)
    obj=db.scalar(select(__import__("app.modules.commerce.models",fromlist=["SalesDocument"]).SalesDocument).where(__import__("app.modules.commerce.models",fromlist=["SalesDocument"]).SalesDocument.id==document_id,__import__("app.modules.commerce.models",fromlist=["SalesDocument"]).SalesDocument.company_id==company_id))
    if obj is None: raise HTTPException(404,"Opportunity not found")
    if obj.document_type!="quotation": raise HTTPException(409,"Only quotations can be advanced from CRM")
    # Preserve the original quotation; create the next commercial document from the same lines.
    lines=[{"item_id":l.item_id,"variant_id":l.variant_id,"tax_rate_ids":getattr(l,"tax_rate_ids",None),"quantity":l.quantity,"unit_price":l.unit_price,"discount_percent":l.discount_percent,"tax_percent":0,"description":l.description} for l in obj.lines]
    payload=DocumentCreate(company_id=company_id,partner_id=obj.partner_id,document_type=target,number=f"CRM-{target.upper()}-{obj.id}-{date.today().strftime('%Y%m%d')}",document_date=date.today(),due_date=obj.due_date,warehouse_id=obj.warehouse_id,notes=obj.notes,lines=lines)
    created=commerce_service.create_document(db,payload); db.commit(); db.refresh(created); return created
