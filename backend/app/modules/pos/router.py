from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .schemas import OutletCreate,TerminalCreate,SessionCreate,POSOrderCreate,POSPaymentCreate
from .service import pos_service
router=APIRouter()
@router.post("/outlets",status_code=201)
def outlet(p:OutletCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return pos_service.create_outlet(db,p,current_user)
@router.post("/terminals",status_code=201)
def terminal(p:TerminalCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return pos_service.create_terminal(db,p,current_user)
@router.post("/sessions/open",status_code=201)
def open_session(p:SessionCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return pos_service.open_session(db,p,current_user)
@router.post("/orders",status_code=201)
def order(p:POSOrderCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return pos_service.create_order(db,p,current_user)
@router.post("/orders/{order_id}/pay")
def pay(order_id:int,p:POSPaymentCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return pos_service.pay_and_issue(db,order_id,p,current_user)
