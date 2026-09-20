from datetime import date
from fastapi import APIRouter,Depends,Query,HTTPException
from pydantic import BaseModel,Field
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.companies.models import Company
from app.modules.commerce.models import BusinessPartner
from app.core.permissions import require_permission
from .completion_service import manufacturing_completion_service
from app.modules.completion.domain_models import ManufacturingWorkOrder
from app.modules.accounting.journals.models import JournalEntry
from app.modules.accounting.journals.services.journal_service import journal_service
from app.modules.inventory.stock_moves.schemas import StockMoveCreate

router=APIRouter(prefix="/manufacturing/completion",tags=["Manufacturing Completion"],dependencies=[Depends(require_permission("manufacturing.access"))])

def _company_for_user(db:Session,company_id:int,u:User):
    if u.tenant_id is None: raise HTTPException(403,"Tenant required")
    x=db.scalar(select(Company).where(Company.id==company_id,Company.tenant_id==u.tenant_id,Company.is_active.is_(True)))
    if x is None: raise HTTPException(403,"Company is outside the current tenant")
    return x

class Labor(BaseModel):
    work_date:date
    user_id:int|None=None
    minutes:float=Field(gt=0)
    hourly_rate:float=Field(ge=0)
class Overhead(BaseModel):
    cost_code:str=Field(min_length=1,max_length=80)
    amount:float=Field(ge=0)
    description:str|None=None
class Scrap(BaseModel):
    item_id:int=Field(gt=0);variant_id:int|None=None;quantity:float=Field(gt=0);unit_cost:float=Field(ge=0);reason:str=Field(min_length=1,max_length=300);stock_move_id:int|None=None;source_location_id:int|None=Field(default=None,gt=0)
class ByProduct(BaseModel):
    item_id:int=Field(gt=0);variant_id:int|None=None;quantity:float=Field(gt=0);unit_cost:float=Field(ge=0);stock_move_id:int|None=None;destination_location_id:int|None=Field(default=None,gt=0)
class GLVariance(BaseModel):
    journal_id:int=Field(gt=0);fiscal_year_id:int=Field(gt=0);period_id:int=Field(gt=0);branch_id:int=Field(gt=0);entry_number:str=Field(min_length=1,max_length=80);entry_date:date;debit_account_id:int=Field(gt=0);credit_account_id:int=Field(gt=0)
class Subcontract(BaseModel):
    vendor_id:int=Field(gt=0);service_reference:str=Field(min_length=1,max_length=120);planned_quantity:float=Field(gt=0);actual_quantity:float=Field(ge=0);unit_cost:float=Field(ge=0);status:str="planned"

@router.post("/work-orders/{work_order_id}/labor",dependencies=[Depends(require_permission("manufacturing.write"))])
def labor(work_order_id:int,p:Labor,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    _company_for_user(db,company_id,u)
    x=manufacturing_completion_service.labor(db,company_id,work_order_id,**p.model_dump());db.commit();db.refresh(x);return x
@router.post("/work-orders/{work_order_id}/overhead",dependencies=[Depends(require_permission("manufacturing.write"))])
def overhead(work_order_id:int,p:Overhead,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    _company_for_user(db,company_id,u)
    x=manufacturing_completion_service.overhead(db,company_id,work_order_id,**p.model_dump());db.commit();db.refresh(x);return x
@router.post("/work-orders/{work_order_id}/scrap",dependencies=[Depends(require_permission("manufacturing.write"))])
def scrap(work_order_id:int,p:Scrap,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    _company_for_user(db,company_id,u)
    if p.source_location_id is not None:
        payload=StockMoveCreate(company_id=company_id,item_id=p.item_id,variant_id=p.variant_id,source_location_id=p.source_location_id,destination_location_id=None,quantity=Decimal(str(p.quantity)),unit_cost=Decimal(str(p.unit_cost)),movement_type="issue",notes=p.reason)
        x=manufacturing_completion_service.stock_backed_scrap(db,u.tenant_id,company_id,work_order_id,payload,u.id)
    else:
        x=manufacturing_completion_service.scrap(db,company_id,work_order_id,**p.model_dump(exclude={"source_location_id"}))
    db.commit();db.refresh(x);return x
@router.post("/work-orders/{work_order_id}/byproducts",dependencies=[Depends(require_permission("manufacturing.write"))])
def byproducts(work_order_id:int,p:ByProduct,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    _company_for_user(db,company_id,u)
    if p.destination_location_id is not None:
        payload=StockMoveCreate(company_id=company_id,item_id=p.item_id,variant_id=p.variant_id,source_location_id=None,destination_location_id=p.destination_location_id,quantity=Decimal(str(p.quantity)),unit_cost=Decimal(str(p.unit_cost)),movement_type="receipt",notes="Manufacturing by-product receipt")
        x=manufacturing_completion_service.stock_backed_byproduct(db,u.tenant_id,company_id,work_order_id,payload,u.id)
    else:
        x=manufacturing_completion_service.byproduct(db,company_id,work_order_id,**p.model_dump(exclude={"destination_location_id"}))
    db.commit();db.refresh(x);return x
@router.post("/work-orders/{work_order_id}/subcontract",dependencies=[Depends(require_permission("manufacturing.write"))])
def subcontract(work_order_id:int,p:Subcontract,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    _company_for_user(db,company_id,u)
    vendor=db.scalar(select(BusinessPartner).where(BusinessPartner.id==p.vendor_id,BusinessPartner.company_id==company_id,BusinessPartner.partner_type.in_(["vendor","both"]),BusinessPartner.is_active.is_(True)))
    if vendor is None: raise HTTPException(422,"Subcontract vendor must be an active vendor of the selected company")
    if p.actual_quantity > p.planned_quantity and p.status != "received": raise HTTPException(422,"Actual subcontract quantity cannot exceed planned quantity unless received")
    x=manufacturing_completion_service.subcontract(db,company_id,work_order_id,**p.model_dump());db.commit();db.refresh(x);return x
@router.post("/work-orders/{work_order_id}/variance",dependencies=[Depends(require_permission("manufacturing.post"))])
def variance(work_order_id:int,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    _company_for_user(db,company_id,u)
    x=manufacturing_completion_service.variance(db,company_id,work_order_id);db.commit();db.refresh(x);return x

@router.post("/work-orders/{work_order_id}/variance/post",dependencies=[Depends(require_permission("manufacturing.post"))])
def post_variance(work_order_id:int,p:GLVariance,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    _company_for_user(db,company_id,u)
    x=manufacturing_completion_service.post_variance(db,company_id,work_order_id,tenant_id=u.tenant_id,user_id=u.id,**p.model_dump());db.commit();db.refresh(x);return x

class Settlement(BaseModel):
    journal_id:int=Field(gt=0);fiscal_year_id:int=Field(gt=0);period_id:int=Field(gt=0);branch_id:int=Field(gt=0);entry_number:str=Field(min_length=1,max_length=80);entry_date:date;wip_account_id:int=Field(gt=0);finished_goods_account_id:int=Field(gt=0)

@router.post("/work-orders/{work_order_id}/wip/settle",dependencies=[Depends(require_permission("manufacturing.post"))])
def settle_wip(work_order_id:int,p:Settlement,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    _company_for_user(db,company_id,u)
    wo=db.get(ManufacturingWorkOrder,work_order_id)
    if wo is None or wo.company_id != company_id: raise HTTPException(404,"Work order not found")
    v=manufacturing_completion_service.variance(db,company_id,work_order_id)
    if v.wip_journal_entry_id:
        existing_entry=db.scalar(select(__import__("app.modules.accounting.journals.models",fromlist=["JournalEntry"]).JournalEntry).where(__import__("app.modules.accounting.journals.models",fromlist=["JournalEntry"]).JournalEntry.id==v.wip_journal_entry_id,__import__("app.modules.accounting.journals.models",fromlist=["JournalEntry"]).JournalEntry.tenant_id==u.tenant_id,__import__("app.modules.accounting.journals.models",fromlist=["JournalEntry"]).JournalEntry.company_id==company_id).with_for_update())
        if existing_entry is None: raise HTTPException(409,"WIP settlement journal entry was not found")
        if existing_entry.status=="posted": return v
        if existing_entry.status=="pending": raise HTTPException(409,"WIP settlement journal is awaiting approval")
        if existing_entry.status=="approved":
            journal_service.post(db,tenant_id=u.tenant_id,entry_id=existing_entry.id,user_id=u.id,commit=False)
            db.commit();db.refresh(v);return v
        raise HTTPException(409,f"WIP settlement journal is in {existing_entry.status} status")
    total=Decimal(v.actual_material or 0)+Decimal(v.actual_labor or 0)+Decimal(v.actual_overhead or 0)-Decimal(v.byproduct_credit or 0)
    if total <= 0: raise HTTPException(409,"No positive WIP balance to settle")
    entry=journal_service.create_draft(db,tenant_id=u.tenant_id,company_id=company_id,branch_id=p.branch_id,journal_id=p.journal_id,fiscal_year_id=p.fiscal_year_id,period_id=p.period_id,entry_number=p.entry_number,entry_date=p.entry_date,description=f"WIP settlement for work order {work_order_id}",lines=[{"account_combination_id":p.wip_account_id,"debit":0,"credit":total},{"account_combination_id":p.finished_goods_account_id,"debit":total,"credit":0}],user_id=u.id,source_module="manufacturing",source_entity="wip_settlement",source_id=work_order_id,commit=False)
    journal_service.submit(db,tenant_id=u.tenant_id,entry_id=entry.id,user_id=u.id,commit=False)
    v.wip_journal_entry_id=entry.id
    if entry.journal.requires_approval:
        db.commit();db.refresh(v);return v
    journal_service.post(db,tenant_id=u.tenant_id,entry_id=entry.id,user_id=u.id,commit=False)
    db.commit();db.refresh(v);return v

class ProductionPayload(BaseModel):
    quantity:Decimal=Field(gt=0)
    source_location_id:int|None=Field(default=None,gt=0)
    destination_location_id:int|None=Field(default=None,gt=0)
    idempotency_key:str|None=Field(default=None,min_length=8,max_length=180)

@router.post("/work-orders/{work_order_id}/produce",dependencies=[Depends(require_permission("manufacturing.post"))])
def produce(work_order_id:int,p:ProductionPayload,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    _company_for_user(db,company_id,u)
    result=manufacturing_completion_service.execute_production(db,u.tenant_id,company_id,work_order_id,u.id,p.quantity,p.source_location_id,p.destination_location_id,p.idempotency_key)
    db.commit()
    return result

class FinalizePayload(BaseModel):
    close_status:str="closed"

@router.post("/work-orders/{work_order_id}/finalize",dependencies=[Depends(require_permission("manufacturing.post"))])
def finalize_work_order(work_order_id:int,p:FinalizePayload,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    _company_for_user(db,company_id,u)
    wo=db.scalar(select(ManufacturingWorkOrder).where(ManufacturingWorkOrder.id==work_order_id,ManufacturingWorkOrder.company_id==company_id).with_for_update())
    if wo is None: raise HTTPException(404,"Work order not found")
    if p.close_status != "closed": raise HTTPException(422,"Finalization status must be closed")
    if getattr(wo,"status",None)=="cancelled": raise HTTPException(409,"Cancelled work orders cannot be finalized")
    if getattr(wo,"status",None)=="closed": return {"work_order_id":wo.id,"status":wo.status,"variance_id":None}
    if Decimal(wo.completed_qty or 0) < Decimal(wo.planned_qty or 0): raise HTTPException(409,"Work order cannot be finalized before planned quantity is fully produced")
    v=manufacturing_completion_service.variance(db,company_id,work_order_id)
    if v.status == "pending_approval":
        raise HTTPException(409, "Manufacturing variance is awaiting independent journal approval before finalization")
    if v.wip_journal_entry_id:
        wip_entry=db.scalar(select(JournalEntry).where(
            JournalEntry.id==v.wip_journal_entry_id,
            JournalEntry.tenant_id==u.tenant_id,
            JournalEntry.company_id==company_id,
        ))
        if wip_entry is None:
            raise HTTPException(409, "WIP settlement journal entry was not found")
        if wip_entry.status != "posted":
            raise HTTPException(409, "WIP settlement must be posted before the work order can be finalized")
    wo.status=p.close_status
    db.commit()
    return {"work_order_id":wo.id,"status":wo.status,"variance_id":v.id,"total_variance":v.total_variance}
