from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.commerce.schemas import PartnerCreate, PartnerResponse, DocumentCreate, DocumentResponse, PaymentCreate
from app.modules.commerce.service import commerce_service

router=APIRouter(prefix='/commerce',tags=['Commerce'])
def run(fn):
    try: return fn()
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc

@router.post('/partners',response_model=PartnerResponse,status_code=201)
def create_partner(payload: PartnerCreate, db: Session=Depends(get_db)):
    obj=run(lambda: commerce_service.create_partner(db,payload)); db.commit(); db.refresh(obj); return obj

@router.get('/partners',response_model=list[PartnerResponse])
def list_partners(company_id:int=Query(...,gt=0),partner_type:str|None=None,db:Session=Depends(get_db)):
    return commerce_service.list_partners(db,company_id,partner_type)

@router.post('/sales/documents',response_model=DocumentResponse,status_code=201)
def create_sale(payload:DocumentCreate,db:Session=Depends(get_db)):
    if payload.document_type not in {'quotation','order','delivery','invoice','credit_note'}: raise HTTPException(400,'Invalid sales document type')
    obj=run(lambda: commerce_service.create_document(db,payload)); db.commit(); db.refresh(obj); return obj

@router.post('/purchases/documents',response_model=DocumentResponse,status_code=201)
def create_purchase(payload:DocumentCreate,db:Session=Depends(get_db)):
    if payload.document_type not in {'requisition','rfq','order','receipt','bill','debit_note'}: raise HTTPException(400,'Invalid purchase document type')
    obj=run(lambda: commerce_service.create_document(db,payload)); db.commit(); db.refresh(obj); return obj

@router.get('/sales/documents',response_model=list[DocumentResponse])
def sales(company_id:int=Query(...,gt=0),db:Session=Depends(get_db)): return commerce_service.list_documents(db,company_id,'sale')
@router.get('/purchases/documents',response_model=list[DocumentResponse])
def purchases(company_id:int=Query(...,gt=0),db:Session=Depends(get_db)): return commerce_service.list_documents(db,company_id,'purchase')

@router.post('/sales/{document_id}/confirm',response_model=DocumentResponse)
def confirm_sale(document_id:int,company_id:int=Query(...,gt=0),db:Session=Depends(get_db)):
    obj=run(lambda: commerce_service.confirm(db,company_id,document_id,'sale')); db.commit(); db.refresh(obj); return obj
@router.post('/purchases/{document_id}/confirm',response_model=DocumentResponse)
def confirm_purchase(document_id:int,company_id:int=Query(...,gt=0),db:Session=Depends(get_db)):
    obj=run(lambda: commerce_service.confirm(db,company_id,document_id,'purchase')); db.commit(); db.refresh(obj); return obj
@router.post('/sales/{document_id}/post-inventory',response_model=DocumentResponse)
def post_sale(document_id:int,company_id:int=Query(...,gt=0),db:Session=Depends(get_db)):
    obj=run(lambda: commerce_service.post_inventory(db,company_id,document_id,'sale')); db.commit(); db.refresh(obj); return obj
@router.post('/purchases/{document_id}/receive',response_model=DocumentResponse)
def receive_purchase(document_id:int,company_id:int=Query(...,gt=0),db:Session=Depends(get_db)):
    obj=run(lambda: commerce_service.post_inventory(db,company_id,document_id,'purchase')); db.commit(); db.refresh(obj); return obj
@router.post('/sales/{document_id}/payments',response_model=DocumentResponse)
def pay_sale(document_id:int,payload:PaymentCreate,db:Session=Depends(get_db)):
    if payload.document_id!=document_id: raise HTTPException(400,'Document id mismatch')
    obj=run(lambda: commerce_service.pay(db,payload,'sale')); db.commit(); db.refresh(obj); return obj
@router.post('/purchases/{document_id}/payments',response_model=DocumentResponse)
def pay_purchase(document_id:int,payload:PaymentCreate,db:Session=Depends(get_db)):
    if payload.document_id!=document_id: raise HTTPException(400,'Document id mismatch')
    obj=run(lambda: commerce_service.pay(db,payload,'purchase')); db.commit(); db.refresh(obj); return obj
