from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.commerce.schemas import PartnerCreate, PartnerResponse, DocumentCreate, DocumentResponse, PaymentCreate, PaymentReverse
from app.modules.commerce.service import commerce_service
from app.modules.commerce.accounting_service import commerce_accounting_service
from app.modules.commerce.accounting_models import CommerceAccountingSettings
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from sqlalchemy import select

router = APIRouter(prefix="/commerce", tags=["Commerce"])


def run(fn):
    try:
        return fn()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/accounting-settings", status_code=201)
def configure_accounting(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    required = ["company_id", "sales_journal_id", "purchase_journal_id", "cash_journal_id", "ar_account_id", "ap_account_id", "sales_account_id", "purchase_account_id", "inventory_account_id", "cogs_account_id", "output_vat_account_id", "input_vat_account_id", "default_payment_account_id", "default_branch_id"]
    if any(k not in payload for k in required):
        raise HTTPException(422, "Missing commerce accounting configuration fields")
    obj = db.scalar(select(CommerceAccountingSettings).where(CommerceAccountingSettings.company_id == payload["company_id"]))
    if obj is None:
        obj = CommerceAccountingSettings(**payload)
        db.add(obj)
    else:
        for key, value in payload.items():
            if hasattr(obj, key) and key != "id":
                setattr(obj, key, value)
    db.flush(); db.commit(); db.refresh(obj)
    return {"id": obj.id, "company_id": obj.company_id, "auto_post": obj.auto_post}


@router.get("/accounting-settings")
def get_accounting_settings(company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    obj = db.scalar(select(CommerceAccountingSettings).where(CommerceAccountingSettings.company_id == company_id))
    if obj is None:
        raise HTTPException(404, "Commerce accounting configuration not found")
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns if c.name != "id"}


@router.post("/partners", response_model=PartnerResponse, status_code=201)
def create_partner(payload: PartnerCreate, db: Session = Depends(get_db)):
    obj = run(lambda: commerce_service.create_partner(db, payload)); db.commit(); db.refresh(obj); return obj


@router.get("/partners", response_model=list[PartnerResponse])
def list_partners(company_id: int = Query(..., gt=0), partner_type: str | None = None, db: Session = Depends(get_db)):
    return commerce_service.list_partners(db, company_id, partner_type)


@router.post("/sales/documents", response_model=DocumentResponse, status_code=201)
def create_sale(payload: DocumentCreate, db: Session = Depends(get_db)):
    if payload.document_type not in {"quotation", "order", "delivery", "invoice", "credit_note"}: raise HTTPException(400, "Invalid sales document type")
    obj = run(lambda: commerce_service.create_document(db, payload)); db.commit(); db.refresh(obj); return obj


@router.post("/purchases/documents", response_model=DocumentResponse, status_code=201)
def create_purchase(payload: DocumentCreate, db: Session = Depends(get_db)):
    if payload.document_type not in {"requisition", "rfq", "order", "receipt", "bill", "debit_note"}: raise HTTPException(400, "Invalid purchase document type")
    obj = run(lambda: commerce_service.create_document(db, payload)); db.commit(); db.refresh(obj); return obj


@router.get("/sales/documents", response_model=list[DocumentResponse])
def sales(company_id: int = Query(..., gt=0), db: Session = Depends(get_db)): return commerce_service.list_documents(db, company_id, "sale")

@router.get("/purchases/documents", response_model=list[DocumentResponse])
def purchases(company_id: int = Query(..., gt=0), db: Session = Depends(get_db)): return commerce_service.list_documents(db, company_id, "purchase")


@router.post("/sales/{document_id}/confirm", response_model=DocumentResponse)
def confirm_sale(document_id: int, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    obj = run(lambda: commerce_service.confirm(db, company_id, document_id, "sale"))
    if obj.document_type == "invoice": commerce_accounting_service.post_sales_invoice(db, obj, current_user.id)
    db.commit(); db.refresh(obj); return obj


@router.post("/purchases/{document_id}/confirm", response_model=DocumentResponse)
def confirm_purchase(document_id: int, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    obj = run(lambda: commerce_service.confirm(db, company_id, document_id, "purchase"))
    if obj.document_type == "bill": commerce_accounting_service.post_purchase_bill(db, obj, current_user.id)
    db.commit(); db.refresh(obj); return obj


@router.post("/sales/{document_id}/post-inventory", response_model=DocumentResponse)
def post_sale(document_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db)):
    obj = run(lambda: commerce_service.post_inventory(db, company_id, document_id, "sale")); db.commit(); db.refresh(obj); return obj


@router.post("/purchases/{document_id}/receive", response_model=DocumentResponse)
def receive_purchase(document_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db)):
    obj = run(lambda: commerce_service.post_inventory(db, company_id, document_id, "purchase")); db.commit(); db.refresh(obj); return obj


@router.post("/sales/{document_id}/payments", response_model=DocumentResponse)
def pay_sale(document_id: int, payload: PaymentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.document_id != document_id: raise HTTPException(400, "Document id mismatch")
    obj = run(lambda: commerce_service.pay(db, payload, "sale")); db.flush()
    payment = db.scalar(select(__import__("app.modules.commerce.models", fromlist=["CommercePayment"]).CommercePayment).where(__import__("app.modules.commerce.models", fromlist=["CommercePayment"]).CommercePayment.document_id == document_id, __import__("app.modules.commerce.models", fromlist=["CommercePayment"]).CommercePayment.company_id == payload.company_id).order_by(__import__("app.modules.commerce.models", fromlist=["CommercePayment"]).CommercePayment.id.desc()))
    if payment: commerce_accounting_service.post_payment(db, payment, obj, current_user.id)
    db.commit(); db.refresh(obj); return obj


@router.post("/purchases/{document_id}/payments", response_model=DocumentResponse)
def pay_purchase(document_id: int, payload: PaymentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.document_id != document_id: raise HTTPException(400, "Document id mismatch")
    obj = run(lambda: commerce_service.pay(db, payload, "purchase")); db.flush()
    payment = db.scalar(select(__import__("app.modules.commerce.models", fromlist=["CommercePayment"]).CommercePayment).where(__import__("app.modules.commerce.models", fromlist=["CommercePayment"]).CommercePayment.document_id == document_id, __import__("app.modules.commerce.models", fromlist=["CommercePayment"]).CommercePayment.company_id == payload.company_id).order_by(__import__("app.modules.commerce.models", fromlist=["CommercePayment"]).CommercePayment.id.desc()))
    if payment: commerce_accounting_service.post_payment(db, payment, obj, current_user.id)
    db.commit(); db.refresh(obj); return obj


@router.post("/payments/{payment_id}/reverse", response_model=DocumentResponse)
def reverse_payment(payment_id: int, payload: PaymentReverse, db: Session = Depends(get_db)):
    obj = run(lambda: commerce_service.reverse_payment(db, payload.company_id, payment_id, payload.reversal_date, payload.notes)); db.commit(); db.refresh(obj); return obj
