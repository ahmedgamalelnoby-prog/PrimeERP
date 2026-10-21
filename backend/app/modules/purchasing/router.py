from datetime import date
from fastapi import APIRouter,Depends,status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .schemas import SupplierCreate,SupplierResponse,PurchaseOrderCreate,PurchaseOrderResponse,ReceiptCreate,ReceiptResponse,PurchaseInvoiceCreate,PurchaseInvoicePost,PurchaseInvoiceResponse
from .service import purchasing_service
router=APIRouter()
@router.get("/suppliers",response_model=list[SupplierResponse])
def suppliers(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return purchasing_service.suppliers(db,current_user)
@router.post("/suppliers",response_model=SupplierResponse,status_code=status.HTTP_201_CREATED)
def create_supplier(p:SupplierCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return purchasing_service.create_supplier(db,p,current_user)
@router.get("/purchase-orders",response_model=list[PurchaseOrderResponse])
def orders(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return purchasing_service.list_orders(db,current_user)
@router.post("/purchase-orders",response_model=PurchaseOrderResponse,status_code=201)
def create_order(p:PurchaseOrderCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return purchasing_service.create_order(db,p,current_user)
@router.post("/purchase-orders/{order_id}/confirm",response_model=PurchaseOrderResponse)
def confirm(order_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return purchasing_service.confirm(db,order_id,current_user)
@router.post("/purchase-receipts",response_model=ReceiptResponse,status_code=201)
def receive(p:ReceiptCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return purchasing_service.receive(db,p,current_user)
@router.post("/purchase-invoices",response_model=PurchaseInvoiceResponse,status_code=201)
def invoice(p:PurchaseInvoiceCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return purchasing_service.create_invoice(db,p,current_user)
@router.post("/purchase-invoices/{invoice_id}/post",response_model=PurchaseInvoiceResponse)
def post_invoice(invoice_id:int,p:PurchaseInvoicePost,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return purchasing_service.post_invoice(db,invoice_id,p,current_user)
