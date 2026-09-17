from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.documents.models import Document
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.saas.entitlements import require_module
from app.services.application_services import (
    ApplicationServiceError,
    create_document_version,
    request_document,
    share_document,
    trash_document,
)

router = APIRouter(prefix="/documents", tags=["Documents"], dependencies=[Depends(require_module("documents"))])


class VersionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    storage_uri: str
    created_by_ref: str | None = None
    checksum: str | None = None


class ShareCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    grantee_ref: str
    role: str = "viewer"
    expires_at: datetime | None = None


class RequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company_id: int
    document_name: str
    requested_from_ref: str
    requested_by_ref: str
    due_at: datetime | None = None
    message: str | None = None


def _company(db: Session, user: User, company_id: int) -> Company:
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == get_effective_tenant_id(user)))
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


def _document(db: Session, user: User, document_id: int) -> Document:
    document = db.scalar(
        select(Document).join(Company, Company.id == Document.company_id).where(
            Document.id == document_id,
            Company.tenant_id == get_effective_tenant_id(user),
        )
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


def _error(exc: ApplicationServiceError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@router.get("/{document_id}")
def get_document(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _document(db, current_user, document_id)


@router.post("/{document_id}/versions", status_code=status.HTTP_201_CREATED)
def create_version(document_id: int, payload: VersionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _document(db, current_user, document_id)
    try:
        version = create_document_version(db, document_id=document_id, **payload.model_dump())
        db.commit()
        db.refresh(version)
        return version
    except ApplicationServiceError as exc:
        db.rollback()
        raise _error(exc) from exc


@router.post("/{document_id}/shares", status_code=status.HTTP_201_CREATED)
def share(document_id: int, payload: ShareCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _document(db, current_user, document_id)
    try:
        share_row = share_document(db, document_id=document_id, **payload.model_dump())
        db.commit()
        db.refresh(share_row)
        return share_row
    except ApplicationServiceError as exc:
        db.rollback()
        raise _error(exc) from exc


@router.post("/requests", status_code=status.HTTP_201_CREATED)
def create_request(payload: RequestCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company(db, current_user, payload.company_id)
    request = request_document(db, **payload.model_dump())
    db.commit()
    db.refresh(request)
    return request


@router.post("/{document_id}/trash")
def trash(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _document(db, current_user, document_id)
    try:
        document = trash_document(db, document_id=document_id)
        db.commit()
        db.refresh(document)
        return document
    except ApplicationServiceError as exc:
        db.rollback()
        raise _error(exc) from exc
