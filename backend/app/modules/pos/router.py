from fastapi import APIRouter,Depends,HTTPException
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.pos.schemas import OutletCreate,DeviceCreate,SessionOpen,OrderCreate,PaymentCreate,SessionClose
from app.modules.pos.service import pos_service
router=APIRouter(prefix="/pos",tags=["POS"],dependencies=[Depends(require_permission("commerce.access"))])
def run(fn):
    try:return fn()
    except ValueError as e:raise HTTPException(400,str(e))
@router.post("/outlets")
def outlet(p:OutletCreate,user:User=Depends(get_current_user),db=Depends(get_db)):
    o=run(lambda:pos_service.create_outlet(db,p,user));db.commit();db.refresh(o);return o
@router.post("/devices")
def device(p:DeviceCreate,user:User=Depends(get_current_user),db=Depends(get_db)):
    d=run(lambda:pos_service.create_device(db,p,user));db.commit();db.refresh(d);return d
@router.post("/sessions/open")
def open_session(p:SessionOpen,user:User=Depends(get_current_user),db=Depends(get_db)):
    s=run(lambda:pos_service.open_session(db,p,user));db.commit();db.refresh(s);return s
@router.post("/orders")
def order(p:OrderCreate,user:User=Depends(get_current_user),db=Depends(get_db)):
    o=run(lambda:pos_service.create_order(db,p,user));db.commit();db.refresh(o);return o
@router.post("/orders/{order_id}/finalize")
def finalize(order_id:int,company_id:int,user:User=Depends(get_current_user),db=Depends(get_db)):
    o=run(lambda:pos_service.finalize(db,company_id,order_id,user));db.commit();db.refresh(o);return o
@router.post("/payments")
def payment(p:PaymentCreate,user:User=Depends(get_current_user),db=Depends(get_db)):
    x=run(lambda:pos_service.pay(db,p,user));db.commit();db.refresh(x);return x
@router.post("/sessions/{session_id}/close")
def close(session_id:int,p:SessionClose,user:User=Depends(get_current_user),db=Depends(get_db)):
    s=run(lambda:pos_service.close_session(db,p.company_id,session_id,p.closing_total,user));db.commit();db.refresh(s);return s
