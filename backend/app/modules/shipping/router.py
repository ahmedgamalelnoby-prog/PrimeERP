from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.products.models import Product
from app.modules.companies.models import Company
from app.modules.branches.models import Branch
from app.modules.transactions.services.numbering_service import numbering_service
from .models import ShippingCarrier,ShippingCarrierRule,Shipment,ShipmentItem,ShippingReturn,CarrierSettlement
from .schemas import CarrierCreate,CarrierRuleCreate,ShipmentCreate,StatusChange,ReturnCreate,SettlementCreate
router=APIRouter()
def tenant(u):
 if u.is_platform_admin or u.tenant_id is None: raise HTTPException(403,"An active tenant context is required")
 return u.tenant_id
def carrier(db,t,i):
 x=db.scalar(select(ShippingCarrier).where(ShippingCarrier.id==i,ShippingCarrier.tenant_id==t,ShippingCarrier.is_active.is_(True)))
 if not x: raise HTTPException(404,"Carrier not found")
 return x
@router.get("/carriers")
def carriers(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
 return list(db.scalars(select(ShippingCarrier).where(ShippingCarrier.tenant_id==tenant(current_user)).order_by(ShippingCarrier.name)).all())
@router.post("/carriers",status_code=201)
def create_carrier(p:CarrierCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
 t=tenant(current_user);x=ShippingCarrier(tenant_id=t,**p.model_dump());db.add(x);db.commit();db.refresh(x);return x
@router.post("/carrier-rules",status_code=201)
def create_rule(p:CarrierRuleCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
 t=tenant(current_user);carrier(db,t,p.carrier_id);x=ShippingCarrierRule(tenant_id=t,**p.model_dump());db.add(x);db.commit();db.refresh(x);return x
@router.post("/shipments",status_code=201)
def create_shipment(p:ShipmentCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
 t=tenant(current_user)
 if not db.scalar(select(Company).where(Company.id==p.company_id,Company.tenant_id==t)):raise HTTPException(404,"Company not found")
 if not db.scalar(select(Branch).where(Branch.id==p.branch_id,Branch.company_id==p.company_id,Branch.tenant_id==t)):raise HTTPException(404,"Branch not found for company")
 if p.carrier_id:carrier(db,t,p.carrier_id)
 seq=numbering_service.generate_next_number(db,t,p.company_id,p.branch_id,"SHIPMENT",commit=False)
 x=Shipment(tenant_id=t,shipment_number=seq["generated_number"],created_by=current_user.id,**p.model_dump(exclude={"lines"}));db.add(x);db.flush()
 for l in p.lines:
  if not db.scalar(select(Product).where(Product.id==l.product_id,Product.tenant_id==t,Product.is_active.is_(True))):raise HTTPException(404,f"Product {l.product_id} not found")
  db.add(ShipmentItem(tenant_id=t,shipment_id=x.id,product_id=l.product_id,quantity=l.quantity))
 db.commit();db.refresh(x);return x
@router.post("/shipments/{shipment_id}/status")
def shipment_status(shipment_id:int,p:StatusChange,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
 t=tenant(current_user);x=db.scalar(select(Shipment).where(Shipment.id==shipment_id,Shipment.tenant_id==t))
 if not x:raise HTTPException(404,"Shipment not found")
 allowed={"preparing":{"packing"},"packing":{"shipped"},"shipped":{"delivered","returned"},"delivered":set(),"returned":set()}
 if p.status not in allowed.get(x.status,set()):raise HTTPException(409,f"Invalid shipment transition {x.status}->{p.status}")
 x.status=p.status;now=datetime.now(timezone.utc)
 if p.status=="shipped":x.dispatched_at=now
 if p.status=="delivered":x.delivered_at=now
 db.commit();db.refresh(x);return x
@router.post("/shipments/{shipment_id}/return",status_code=201)
def shipment_return(shipment_id:int,p:ReturnCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
 t=tenant(current_user);x=db.scalar(select(Shipment).where(Shipment.id==shipment_id,Shipment.tenant_id==t))
 if not x:raise HTTPException(404,"Shipment not found")
 if x.status not in ("shipped","delivered"):raise HTTPException(409,"Shipment cannot be returned")
 r=ShippingReturn(tenant_id=t,shipment_id=x.id,reason=p.reason);x.status="returned";x.returned_at=datetime.now(timezone.utc);db.add(r);db.commit();db.refresh(r);return r
@router.post("/carrier-settlements",status_code=201)
def settlement(p:SettlementCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
 t=tenant(current_user);carrier(db,t,p.carrier_id)
 seq=numbering_service.generate_next_number(db,t,p.carrier_id,p.carrier_id,"CARRIER_SETTLEMENT",commit=False)
 x=CarrierSettlement(tenant_id=t,settlement_number=seq["generated_number"],net_amount=p.orders_amount+p.cod_collected-p.carrier_charges,**p.model_dump());db.add(x);db.commit();db.refresh(x);return x
