import json
from datetime import datetime, timezone
from typing import Any

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.audit.service import record_audit_event
from app.modules.commerce.models import BusinessPartner, SalesDocument
from app.modules.companies.models import Company
from .constants import ETA_DOCUMENT_SUBMISSION_PATH, ETA_DOCUMENT_PATH_TEMPLATE, ETA_SUBMISSION_PATH_TEMPLATE, SUPPORTED_STATUSES
from .models import EgyptianEInvoiceDocument


class ETAIntegrationError(RuntimeError):
    pass


_TERMINAL_STATUSES = {"valid", "rejected", "cancelled"}


def _terminal_status_cannot_regress(current: str, incoming: str) -> bool:
    return current in _TERMINAL_STATUSES and incoming != current


class ETAClient:
    def _token(self) -> str:
        if not settings.ETA_ENABLED:
            raise ETAIntegrationError("ETA integration is disabled")
        response = requests.post(
            settings.ETA_IDENTITY_URL,
            data={"grant_type": "client_credentials", "client_id": settings.ETA_CLIENT_ID, "client_secret": settings.ETA_CLIENT_SECRET},
            headers={"Accept": "application/json"},
            timeout=30,
            verify=True,
        )
        if response.status_code != 200:
            raise ETAIntegrationError(f"ETA authentication failed with HTTP {response.status_code}")
        data = response.json()
        token = data.get("access_token")
        if not token:
            raise ETAIntegrationError("ETA authentication response did not contain access_token")
        return token

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        token = self._token()
        headers = dict(kwargs.pop("headers", {}) or {})
        headers.update({"Authorization": f"Bearer {token}", "Accept": "application/json"})
        return requests.request(method, f"{settings.ETA_API_BASE_URL.rstrip('/')}{path}", headers=headers, timeout=30, verify=True, **kwargs)

    def submit(self, signed_documents: list[dict]) -> dict:
        if not signed_documents:
            raise ETAIntegrationError("At least one signed document is required")
        response = self._request("POST", ETA_DOCUMENT_SUBMISSION_PATH, json={"documents": signed_documents}, headers={"Content-Type": "application/json"})
        try:
            body = response.json()
        except ValueError:
            body = {"raw": response.text[:4000]}
        if response.status_code not in {200, 202}:
            raise ETAIntegrationError(f"ETA submission failed with HTTP {response.status_code}: {body}")
        return body

    def get_document(self, eta_uuid: str) -> dict:
        response = self._request("GET", ETA_DOCUMENT_PATH_TEMPLATE.format(uuid=eta_uuid))
        if response.status_code != 200:
            raise ETAIntegrationError(f"ETA document retrieval failed with HTTP {response.status_code}")
        return response.json()

    def get_submission(self, submission_uuid: str) -> dict:
        response = self._request("GET", ETA_SUBMISSION_PATH_TEMPLATE.format(uuid=submission_uuid))
        if response.status_code != 200:
            raise ETAIntegrationError(f"ETA submission retrieval failed with HTTP {response.status_code}")
        return response.json()


eta_client = ETAClient()


def create_document(db: Session, *, tenant_id: int, company_id: int, source_type: str, source_id: int, document_type: str, internal_number: str, signed_payload: str) -> EgyptianEInvoiceDocument:
    normalized_source_type = source_type.strip().lower()
    normalized_document_type = document_type.strip().lower()
    if normalized_source_type not in {"sales_document", "sale", "sales_invoice"}:
        raise ValueError("Unsupported ETA source type")

    company_tenant_id = db.scalar(select(Company.tenant_id).where(Company.id == company_id))
    if company_tenant_id is None or company_tenant_id != tenant_id:
        raise ValueError("ETA company does not belong to the tenant")

    source = db.scalar(select(SalesDocument).where(SalesDocument.id == source_id, SalesDocument.company_id == company_id))
    if source is None:
        raise ValueError("ETA source sales document does not belong to the company")
    if source.document_type not in {"invoice", "credit_note"}:
        raise ValueError("Only sales invoices and credit notes can be submitted to ETA")
    if normalized_document_type not in {"invoice", "credit_note"} or normalized_document_type != source.document_type:
        raise ValueError("ETA document type does not match the source sales document")
    if not internal_number.strip():
        raise ValueError("ETA internal number is required")
    obj = EgyptianEInvoiceDocument(
        tenant_id=tenant_id,
        company_id=company_id,
        source_type="sales_document",
        source_id=source_id,
        document_type=normalized_document_type,
        internal_number=internal_number.strip(),
        signed_payload=signed_payload,
        status="draft",
    )
    db.add(obj)
    db.flush()
    return obj


def submit_document(db: Session, obj: EgyptianEInvoiceDocument, *, user_id: int | None = None, tenant_id: int | None = None) -> EgyptianEInvoiceDocument:
    if obj.status not in {"draft", "error", "rejected"}:
        raise ETAIntegrationError(f"Document cannot be submitted from status {obj.status}")
    if not obj.signed_payload:
        raise ETAIntegrationError("A digitally signed ETA payload is required before submission")
    payload = json.loads(obj.signed_payload)
    obj.status = "queued"
    db.flush()
    try:
        result = eta_client.submit([payload])
        obj.eta_response = json.dumps(result, ensure_ascii=False, default=str)
        obj.submission_uuid = result.get("submissionUUID") or result.get("submissionUuid")
        accepted = result.get("acceptedDocuments") or []
        rejected = result.get("rejectedDocuments") or []
        if rejected and not accepted:
            obj.status = "rejected"
            first = rejected[0] if isinstance(rejected[0], dict) else {}
            obj.error_code = str(first.get("code") or first.get("errorCode") or "ETA_REJECTED")
            obj.error_message = str(first.get("error") or first.get("message") or "ETA rejected the document")
        else:
            obj.status = "submitted"
            if accepted and isinstance(accepted[0], dict):
                obj.eta_uuid = accepted[0].get("uuid") or accepted[0].get("UUID")
        obj.submitted_at = datetime.now(timezone.utc)
        obj.error_code = None if obj.status == "submitted" else obj.error_code
        obj.error_message = None if obj.status == "submitted" else obj.error_message
        obj.retry_count = 0
        record_audit_event(db, action="einvoice.submit", entity_type="egyptian_einvoice", entity_id=obj.id, user_id=user_id, tenant_id=tenant_id, company_id=obj.company_id, metadata={"status": obj.status, "submission_uuid": obj.submission_uuid, "eta_uuid": obj.eta_uuid})
        return obj
    except (ETAIntegrationError, ValueError, json.JSONDecodeError) as exc:
        obj.status = "error"
        obj.retry_count += 1
        obj.error_code = "ETA_CLIENT_ERROR"
        obj.error_message = str(exc)[:4000]
        record_audit_event(db, action="einvoice.submit_error", entity_type="egyptian_einvoice", entity_id=obj.id, user_id=user_id, tenant_id=tenant_id, company_id=obj.company_id, metadata={"error": str(exc)[:1000], "retry_count": obj.retry_count})
        raise


def sync_status(db: Session, obj: EgyptianEInvoiceDocument, *, user_id: int | None = None, tenant_id: int | None = None) -> EgyptianEInvoiceDocument:
    if obj.eta_uuid:
        result = eta_client.get_document(obj.eta_uuid)
    elif obj.submission_uuid:
        result = eta_client.get_submission(obj.submission_uuid)
    else:
        raise ETAIntegrationError("Document has neither ETA UUID nor submission UUID")
    obj.eta_response = json.dumps(result, ensure_ascii=False, default=str)
    status_value = str(result.get("status") or result.get("Status") or "submitted").lower()
    mapping = {"valid": "valid", "issued": "valid", "rejected": "rejected", "cancelled": "cancelled", "invalid": "rejected"}
    incoming_status = mapping.get(status_value, "submitted")
    if not _terminal_status_cannot_regress(obj.status, incoming_status):
        obj.status = incoming_status
    if obj.status == "valid":
        obj.validated_at = datetime.now(timezone.utc)
    errors = result.get("validationResults") or result.get("error") or result.get("errors")
    if obj.status == "rejected" and errors:
        obj.error_message = str(errors)[:4000]
    if obj.status not in SUPPORTED_STATUSES:
        obj.status = "error"
    record_audit_event(db, action="einvoice.status_sync", entity_type="egyptian_einvoice", entity_id=obj.id, user_id=user_id, tenant_id=tenant_id, company_id=obj.company_id, metadata={"status": obj.status, "eta_uuid": obj.eta_uuid, "submission_uuid": obj.submission_uuid})
    return obj
