from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.shipping.models import ShippingCarrier,ShippingMethod,Shipment
from app.modules.shipping.schemas import CarrierCreate,CarrierResponse,MethodCreate,MethodResponse,ShipmentCreate,ShipmentResponse
router=APIRouter(prefix='/shipping',tags=['Shipping'])
@router.post('/carriers',response_model=CarrierResponse,status_code=201)
def carrier(p:CarrierCreate,db:Session=Depends(get_db)):
 o=ShippingCarrier(**p.model_dump());db.add(o);db.commit();db.refresh(o);return o
@router.get('/carriers',response_model=list[CarrierResponse])
def carriers(company_id:int=Query(...,gt=0),db:Session=Depends(get_db)):return list(db.scalars(select(ShippingCarrier).where(ShippingCarrier.company_id==company_id,ShippingCarrier.is_active.is_(True)).order_by(ShippingCarrier.name)).all())
@router.post('/methods',response_model=MethodResponse,status_code=201)
def method(p:MethodCreate,db:Session=Depends(get_db)):
 if not db.get(ShippingCarrier,p.carrier_id):raise HTTPException(400,'Carrier not found')
 o=ShippingMethod(**p.model_dump());db.add(o);db.commit();db.refresh(o);return o
@router.get('/methods',response_model=list[MethodResponse])
def methods(carrier_id:int=Query(...,gt=0),db:Session=Depends(get_db)):return list(db.scalars(select(ShippingMethod).where(ShippingMethod.carrier_id==carrier_id)).all())
@router.post('/shipments',response_model=ShipmentResponse,status_code=201)
def shipment(p:ShipmentCreate,db:Session=Depends(get_db)):
 m=db.get(ShippingMethod,p.method_id)
 if not m or m.carrier_id!=p.carrier_id:raise HTTPException(400,'Invalid carrier/method')
 fee=p.shipping_fee or m.base_fee
 if m.payment_method=='cod' and p.cod_amount:fee+=p.cod_amount*m.cod_fee_percent/100
 o=Shipment(**p.model_dump(),shipping_fee=fee);db.add(o);db.commit();db.refresh(o);return o
@router.get('/shipments',response_model=list[ShipmentResponse])
def shipments(company_id:int=Query(...,gt=0),status:str|None=None,db:Session=Depends(get_db)):
 q=select(Shipment).where(Shipment.company_id==company_id)
 if status:q=q.where(Shipment.status==status)
 return list(db.scalars(q.order_by(Shipment.id.desc())).all())
@router.post('/shipments/{shipment_id}/status',response_model=ShipmentResponse)
def status(shipment_id:int,value:str=Query(...),company_id:int=Query(...,gt=0),db:Session=Depends(get_db)):
 if value not in {'pending','picked_up','in_transit','out_for_delivery','delivered','returned','cancelled'}:raise HTTPException(400,'Invalid shipment status')
 o=db.scalar(select(Shipment).where(Shipment.id==shipment_id,Shipment.company_id==company_id).with_for_update())
 if not o:raise HTTPException(404,'Shipment not found')
 o.status=value;db.commit();db.refresh(o);return o
