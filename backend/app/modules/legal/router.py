from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.legal.models import LegalAcceptance, LegalDocument

router = APIRouter(prefix="/legal", tags=["legal"])

DEFAULTS = {
    "terms": {
        "title_ar": "شروط الاستخدام",
        "title_en": "Terms of Use",
        "content_ar": "اكتب هنا شروط استخدام PrimeERP. يمكنك تعديل هذا النص من إعدادات النظام.",
        "content_en": "Write the PrimeERP Terms of Use here. You can edit this text from System Settings.",
    },
    "privacy": {
        "title_ar": "سياسة الخصوصية",
        "title_en": "Privacy Policy",
        "content_ar": "اكتب هنا سياسة الخصوصية الخاصة بـ PrimeERP. يمكنك تعديل هذا النص من إعدادات النظام.",
        "content_en": "Write the PrimeERP Privacy Policy here. You can edit this text from System Settings.",
    },
}


class LegalUpdateRequest(BaseModel):
    title_ar: str = Field(min_length=1, max_length=200)
    title_en: str = Field(min_length=1, max_length=200)
    content_ar: str = Field(min_length=1)
    content_en: str = Field(min_length=1)
    is_published: bool = True


class LegalAcceptRequest(BaseModel):
    document_type: str = Field(pattern="^(terms|privacy)$")
    version: int = Field(ge=1)


def _get_or_create(db: Session, document_type: str) -> LegalDocument:
    document = db.query(LegalDocument).filter(LegalDocument.document_type == document_type).first()
    if document:
        return document
    default = DEFAULTS[document_type]
    document = LegalDocument(
        document_type=document_type,
        title_ar=default["title_ar"],
        title_en=default["title_en"],
        content_ar=default["content_ar"],
        content_en=default["content_en"],
        version=1,
        is_published=True,
        published_at=datetime.now(timezone.utc),
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def _serialize(document: LegalDocument) -> dict:
    return {
        "id": document.id,
        "document_type": document.document_type,
        "title_ar": document.title_ar,
        "title_en": document.title_en,
        "content_ar": document.content_ar,
        "content_en": document.content_en,
        "version": document.version,
        "is_published": document.is_published,
        "published_at": document.published_at,
        "updated_at": document.updated_at,
    }


def _require_platform_admin(current_user: User) -> User:
    if not current_user.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the platform administrator can manage legal documents.")
    return current_user


@router.get("")
def list_legal_documents(db: Session = Depends(get_db)):
    documents = [_get_or_create(db, "terms"), _get_or_create(db, "privacy")]
    return {"success": True, "data": [_serialize(document) for document in documents]}


@router.get("/acceptance/status")
def legal_acceptance_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = {}
    for document_type in ("terms", "privacy"):
        document = _get_or_create(db, document_type)
        accepted = db.query(LegalAcceptance).filter(
            LegalAcceptance.user_id == current_user.id,
            LegalAcceptance.document_type == document_type,
            LegalAcceptance.document_version == document.version,
        ).first() is not None
        result[document_type] = {"version": document.version, "accepted": accepted}
    return {"success": True, "data": result}


@router.post("/accept")
def accept_legal_document(payload: LegalAcceptRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = _get_or_create(db, payload.document_type)
    if payload.version != document.version:
        raise HTTPException(status_code=409, detail="This legal document version is no longer current.")
    existing = db.query(LegalAcceptance).filter(
        LegalAcceptance.user_id == current_user.id,
        LegalAcceptance.document_type == payload.document_type,
        LegalAcceptance.document_version == payload.version,
    ).first()
    if not existing:
        db.add(LegalAcceptance(user_id=current_user.id, document_type=payload.document_type, document_version=payload.version))
        db.commit()
    return {"success": True, "data": {"document_type": payload.document_type, "version": payload.version, "accepted": True}}


@router.get("/{document_type}")
def get_legal_document(document_type: str, db: Session = Depends(get_db)):
    if document_type not in DEFAULTS:
        raise HTTPException(status_code=404, detail="Legal document not found")
    return {"success": True, "data": _serialize(_get_or_create(db, document_type))}


@router.put("/{document_type}")
def update_legal_document(document_type: str, payload: LegalUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if document_type not in DEFAULTS:
        raise HTTPException(status_code=404, detail="Legal document not found")
    _require_platform_admin(current_user)
    document = _get_or_create(db, document_type)
    document.title_ar = payload.title_ar.strip()
    document.title_en = payload.title_en.strip()
    document.content_ar = payload.content_ar
    document.content_en = payload.content_en
    document.version += 1
    document.is_published = payload.is_published
    document.updated_by = current_user.id
    document.published_at = datetime.now(timezone.utc) if payload.is_published else None
    db.commit()
    db.refresh(document)
    return {"success": True, "message": "Legal document updated.", "data": _serialize(document)}
