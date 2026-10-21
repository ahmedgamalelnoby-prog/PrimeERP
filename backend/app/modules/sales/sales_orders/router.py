from typing import Optional
from fastapi import APIRouter,Depends,Query,status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .schemas import SalesOrderCreate,SalesOrderResponse,SalesOrderAction,SalesOrderFulfill
from .service import sales_order_service
router=APIRouter()
@router.get("/sales-orders",response_model=list[SalesOrderResponse])
def list_orders(order_status:Optional[str]=Query(None,alias="status"),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):return sales_order_service.list(db,current_user,order_status)
@router.post("/sales-orders",response_model=SalesOrderResponse,status_code=status.HTTP_201_CREATED)
def create_order(payload:SalesOrderCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):return sales_order_service.create(db,payload,current_user)
@router.get("/sales-orders/{order_id}",response_model=SalesOrderResponse)
def get_order(order_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):return sales_order_service.get(db,current_user,order_id)
@router.post("/sales-orders/{order_id}/confirm",response_model=SalesOrderResponse)
def confirm(order_id:int,payload:SalesOrderAction,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):return sales_order_service.transition(db,current_user,order_id,"draft","confirmed")
@router.post("/sales-orders/{order_id}/cancel",response_model=SalesOrderResponse)
def cancel(order_id:int,payload:SalesOrderAction,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):return sales_order_service.transition(db,current_user,order_id,"draft","cancelled")
@router.post("/sales-orders/{order_id}/reserve",response_model=SalesOrderResponse)
def reserve(order_id:int,payload:SalesOrderFulfill,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):return sales_order_service.reserve(db,current_user,order_id,payload)
@router.post("/sales-orders/{order_id}/issue",response_model=SalesOrderResponse)
def issue(order_id:int,payload:SalesOrderFulfill,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):return sales_order_service.issue(db,current_user,order_id,payload)