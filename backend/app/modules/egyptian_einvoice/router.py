from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .crud import ETAIntegrationError, create_document, submit_document, sync_status
from .models import EgyptianEInvoiceDocument
from .permissions import EINVOICE_ACCESS, EINVOICE_POST, EINVOICE_WRITE

router = APIRouter(prefix="/egyptian-einvoice", tags=["Egyptian E-Invoicing"])


def _company_for_user(db: Session, company_id: int, user: User) -> Company:
    if user.tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == user.tenant_id, Company.is_active.is_(True)))
    if company is None:
        raise HTTPException(403, "Company is outside the current tenant or inactive")
    return company


@router.get("/documents", dependencies=[Depends(require_permission(EINVOICE_ACCESS))])
def list_documents(company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    return list(db.scalars(select(EgyptianEInvoiceDocument).where(EgyptianEInvoiceDocument.company_id == company_id).order_by(EgyptianEInvoiceDocument.id.desc()).limit(200)).all())


@router.post("/documents", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission(EINVOICE_WRITE))])
def create_eta_document(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company_id = int(payload.get("company_id", 0))
    _company_for_user(db, company_id, current_user)
    required = ("source_type", "source_id", "document_type", "internal_number", "signed_payload")
    missing = [field for field in required if payload.get(field) in (None, "")]
    if missing:
        raise HTTPException(422, f"Missing required fields: {', '.join(missing)}")
    try:
        obj = create_document(db, company_id=company_id, source_type=str(payload["source_type"]), source_id=int(payload["source_id"]), document_type=str(payload["document_type"]), internal_number=str(payload["internal_number"]), signed_payload=str(payload["signed_payload"]))
        db.commit()
        db.refresh(obj)
        return obj
    except (ValueError, TypeError) as exc:
        db.rollback()
        raise HTTPException(422, "Invalid ETA document values") from exc


@router.post("/documents/{document_id}/submit", dependencies=[Depends(require_permission(EINVOICE_POST))])
def submit_eta_document(document_id: int, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    obj = db.scalar(select(EgyptianEInvoiceDocument).where(EgyptianEInvoiceDocument.id == document_id, EgyptianEInvoiceDocument.company_id == company_id).with_for_update())
    if obj is None:
        raise HTTPException(404, "Egyptian e-invoice document not found")
    try:
        submit_document(db, obj, user_id=current_user.id, tenant_id=current_user.tenant_id)
        db.commit()
        db.refresh(obj)
        return obj
    except ETAIntegrationError as exc:
        db.commit()
        raise HTTPException(502, str(exc)) from exc


@router.post("/documents/{document_id}/sync", dependencies=[Depends(require_permission(EINVOICE_POST))])
def sync_eta_document(document_id: int, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    obj = db.scalar(select(EgyptianEInvoiceDocument).where(EgyptianEInvoiceDocument.id == document_id, EgyptianEInvoiceDocument.company_id == company_id).with_for_update())
    if obj is None:
        raise HTTPException(404, "Egyptian e-invoice document not found")
    try:
        sync_status(db, obj, user_id=current_user.id, tenant_id=current_user.tenant_id)
        db.commit()
        db.refresh(obj)
        return obj
    except ETAIntegrationError as exc:
        db.rollback()
        raise HTTPException(502, str(exc)) from exc
