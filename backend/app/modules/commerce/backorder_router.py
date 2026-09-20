from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from .backorder_service import backorder_service
router=APIRouter(prefix="/commerce/backorders",tags=["commerce-backorders"])
@router.get("")
def list_open(kind:str|None=None,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    return backorder_service.list_open(db,current_user.company_id,kind)
@router.post("/{kind}/{document_id}")
def generate(kind:str,document_id:int,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    if kind not in {"sale","purchase"}: raise ValueError("kind must be sale or purchase")
    return backorder_service.generate_for_document(db,company_id=current_user.company_id,document_id=document_id,kind=kind)