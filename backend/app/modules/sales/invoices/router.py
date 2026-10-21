from fastapi import APIRouter,Depends,status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .schemas import InvoiceCreate,InvoiceResponse,InvoicePost
from .service import invoice_service
router=APIRouter()
@router.get("/invoices",response_model=list[InvoiceResponse])
def list_invoices(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):return invoice_service.list(db,current_user)
@router.post("/invoices",response_model=InvoiceResponse,status_code=status.HTTP_201_CREATED)
def create_invoice(payload:InvoiceCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):return invoice_service.create_from_order(db,current_user,payload)
@router.get("/invoices/{invoice_id}",response_model=InvoiceResponse)
def get_invoice(invoice_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):return invoice_service.get(db,current_user,invoice_id)
@router.post("/invoices/{invoice_id}/post",response_model=InvoiceResponse)
def post_invoice(invoice_id:int,payload:InvoicePost,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):return invoice_service.post(db,current_user,invoice_id,payload)