import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .models import IntegrationConnection, IntegrationEvent
from .schemas import ConnectionCreate, ConnectionResponse, WebhookEventCreate

router = APIRouter(prefix="/integrations", tags=["Integrations"])


def _company_for_user(db: Session, company_id: int, user: User):
    if user.tenant_id is None: raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == user.tenant_id))
    if company is None: raise HTTPException(403, "Company is outside the current tenant")
    return company


@router.post("/connections", response_model=ConnectionResponse, status_code=201)
def create_connection(payload: ConnectionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, payload.company_id, current_user)
    if payload.provider.lower() not in {"salla", "generic"}: raise HTTPException(400, "Unsupported provider")
    obj = IntegrationConnection(**payload.model_dump(), provider=payload.provider.lower())
    db.add(obj)
    try:
        db.commit(); db.refresh(obj)
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(409, "Integration connection already exists") from exc
    return obj


@router.get("/connections", response_model=list[ConnectionResponse])
def list_connections(company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    return db.scalars(select(IntegrationConnection).where(IntegrationConnection.company_id == company_id).order_by(IntegrationConnection.id.desc())).all()


@router.post("/salla/{connection_id}/webhook", status_code=202)
def receive_salla_webhook(connection_id: int, payload: WebhookEventCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    connection = db.scalar(select(IntegrationConnection).join(Company, Company.id == IntegrationConnection.company_id).where(IntegrationConnection.id == connection_id, IntegrationConnection.provider == "salla", IntegrationConnection.is_active.is_(True), Company.tenant_id == current_user.tenant_id))
    if not connection: raise HTTPException(404, "Salla connection not found")
    existing = db.scalar(select(IntegrationEvent).where(IntegrationEvent.connection_id == connection_id, IntegrationEvent.external_event_id == payload.external_event_id))
    if existing: return {"accepted": True, "duplicate": True, "event_id": existing.id}
    event = IntegrationEvent(company_id=connection.company_id, connection_id=connection_id, external_event_id=payload.external_event_id, event_type=payload.event_type, payload=json.dumps(payload.payload, ensure_ascii=False), status="received")
    db.add(event); connection.last_sync_at = datetime.now(timezone.utc)
    try:
        db.commit(); db.refresh(event)
    except IntegrityError:
        db.rollback(); return {"accepted": True, "duplicate": True}
    return {"accepted": True, "duplicate": False, "event_id": event.id}


@router.get("/events", status_code=200)
def list_events(company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    return db.scalars(select(IntegrationEvent).where(IntegrationEvent.company_id == company_id).order_by(IntegrationEvent.id.desc()).limit(200)).all()
