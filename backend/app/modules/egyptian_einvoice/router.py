import hmac
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.audit.service import record_audit_event
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .crud import ETAIntegrationError, create_document, submit_document, sync_status
from .models import EgyptianEInvoiceDocument
from .permissions import EINVOICE_ACCESS, EINVOICE_POST, EINVOICE_WRITE

router = APIRouter(prefix="/egyptian-einvoice", tags=["Egyptian E-Invoicing"])


def _company_for_user(db: Session, company_id: int, user: User) -> Company:
    tenant_id = get_effective_tenant_id(user)
    if tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == tenant_id, Company.is_active.is_(True)))
    if company is None:
        raise HTTPException(403, "Company is outside the current tenant or inactive")
    return company


def _require_eta_notification_secret(authorization: str | None = Header(default=None)) -> None:
    if not settings.ETA_ENABLED or not settings.ETA_NOTIFICATION_SECRET:
        raise HTTPException(503, "ETA notification endpoint is not configured")
    expected = f"ApiKey {settings.ETA_NOTIFICATION_SECRET}"
    if not authorization or not hmac.compare_digest(authorization, expected):
        raise HTTPException(401, "Invalid ETA notification authorization")


@router.post("/partners/{partner_id}/verify", dependencies=[Depends(require_permission(EINVOICE_WRITE))])
def verify_partner_tax_identity(partner_id: int, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    from app.modules.commerce.models import BusinessPartner
    partner = db.scalar(select(BusinessPartner).where(BusinessPartner.id == partner_id, BusinessPartner.company_id == company_id))
    if partner is None:
        raise HTTPException(404, "Customer not found")
    if partner.partner_type not in {"customer", "both"}:
        raise HTTPException(422, "ETA customer verification is available for customers")
    if not partner.tax_number:
        raise HTTPException(422, "Customer tax registration number is required")
    # ETA's taxpayer identity is represented by the registration number; the
    # real-time validation call is performed by the configured ETA integration.
    partner.eta_party_id = partner.tax_number
    partner.eta_registration_status = "pending"
    record_audit_event(db, action="einvoice.partner_verify_requested", entity_type="commerce_partner", entity_id=partner.id, user_id=current_user.id, tenant_id=get_effective_tenant_id(current_user), company_id=company_id, metadata={"verification_status": "pending"})
    db.commit()
    db.refresh(partner)
    return {"id": partner.id, "tax_number": partner.tax_number, "commercial_registration_number": partner.commercial_registration_number, "eta_party_id": partner.eta_party_id, "eta_registration_status": partner.eta_registration_status, "eta_last_verified_at": partner.eta_last_verified_at}

@router.get("/documents", dependencies=[Depends(require_permission(EINVOICE_ACCESS))])
def list_documents(company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    return list(db.scalars(select(EgyptianEInvoiceDocument).where(EgyptianEInvoiceDocument.tenant_id == get_effective_tenant_id(current_user), EgyptianEInvoiceDocument.company_id == company_id).order_by(EgyptianEInvoiceDocument.id.desc()).limit(200)).all())


@router.post("/documents", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission(EINVOICE_WRITE))])
def create_eta_document(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company_id = int(payload.get("company_id", 0))
    _company_for_user(db, company_id, current_user)
    required = ("source_type", "source_id", "document_type", "internal_number", "signed_payload")
    missing = [field for field in required if payload.get(field) in (None, "")]
    if missing:
        raise HTTPException(422, f"Missing required fields: {', '.join(missing)}")
    try:
        obj = create_document(db, tenant_id=get_effective_tenant_id(current_user), company_id=company_id, source_type=str(payload["source_type"]), source_id=int(payload["source_id"]), document_type=str(payload["document_type"]), internal_number=str(payload["internal_number"]), signed_payload=str(payload["signed_payload"]))
        record_audit_event(db, action="einvoice.create", entity_type="egyptian_einvoice", entity_id=obj.id, user_id=current_user.id, tenant_id=get_effective_tenant_id(current_user), company_id=company_id, metadata={"source_type": obj.source_type, "source_id": obj.source_id, "document_type": obj.document_type})
        db.commit()
        db.refresh(obj)
        return obj
    except (ValueError, TypeError) as exc:
        db.rollback()
        raise HTTPException(422, "Invalid ETA document values") from exc


@router.post("/documents/{document_id}/submit", dependencies=[Depends(require_permission(EINVOICE_POST))])
def submit_eta_document(document_id: int, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    obj = db.scalar(select(EgyptianEInvoiceDocument).where(EgyptianEInvoiceDocument.id == document_id, EgyptianEInvoiceDocument.tenant_id == get_effective_tenant_id(current_user), EgyptianEInvoiceDocument.company_id == company_id).with_for_update())
    if obj is None:
        raise HTTPException(404, "Egyptian e-invoice document not found")
    try:
        submit_document(db, obj, user_id=current_user.id, tenant_id=get_effective_tenant_id(current_user))
        db.commit()
        db.refresh(obj)
        return obj
    except ETAIntegrationError as exc:
        db.commit()
        raise HTTPException(502, str(exc)) from exc


@router.post("/documents/{document_id}/sync", dependencies=[Depends(require_permission(EINVOICE_POST))])
def sync_eta_document(document_id: int, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    obj = db.scalar(select(EgyptianEInvoiceDocument).where(EgyptianEInvoiceDocument.id == document_id, EgyptianEInvoiceDocument.tenant_id == get_effective_tenant_id(current_user), EgyptianEInvoiceDocument.company_id == company_id).with_for_update())
    if obj is None:
        raise HTTPException(404, "Egyptian e-invoice document not found")
    try:
        sync_status(db, obj, user_id=current_user.id, tenant_id=get_effective_tenant_id(current_user))
        db.commit()
        db.refresh(obj)
        return obj
    except ETAIntegrationError as exc:
        db.rollback()
        raise HTTPException(502, str(exc)) from exc


@router.put("/notifications/documents", status_code=200, dependencies=[Depends(_require_eta_notification_secret)])
def receive_eta_document_notification(payload: dict, authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    _require_eta_notification_secret(authorization)
    eta_uuid = payload.get("uuid") or payload.get("documentUUID") or payload.get("documentUuid")
    if not eta_uuid:
        raise HTTPException(422, "ETA notification uuid is required")

    obj = db.scalar(select(EgyptianEInvoiceDocument).where(EgyptianEInvoiceDocument.eta_uuid == str(eta_uuid)).with_for_update())
    if obj is None:
        return {"received": True, "matched": False}

    status_value = str(payload.get("status") or payload.get("Status") or "submitted").lower()
    mapping = {"valid": "valid", "issued": "valid", "rejected": "rejected", "invalid": "rejected", "cancelled": "cancelled", "submitted": "submitted"}
    new_status = mapping.get(status_value, "error")

    # Do not allow a callback/replay to move a terminal document backwards.
    # ETA resubmission is represented by a new submission/document lifecycle.
    terminal = {"valid", "rejected", "cancelled"}
    if obj.status in terminal and new_status not in terminal:
        return {"received": True, "matched": True, "document_id": obj.id, "status": obj.status, "ignored": True}

    obj.status = new_status
    obj.eta_response = json.dumps(payload, ensure_ascii=False, default=str)
    if obj.status == "valid":
        obj.validated_at = datetime.now(timezone.utc)

    record_audit_event(
        db,
        action="einvoice.notification",
        entity_type="egyptian_einvoice",
        entity_id=obj.id,
        tenant_id=obj.tenant_id,
        company_id=obj.company_id,
        metadata={"eta_uuid": str(eta_uuid), "status": obj.status},
    )
    db.commit()
    return {"received": True, "matched": True, "document_id": obj.id, "status": obj.status}
