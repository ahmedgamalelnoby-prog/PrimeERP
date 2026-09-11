import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database.session import get_db
from .models import IntegrationConnection, IntegrationEvent
from .schemas import ConnectionCreate, ConnectionResponse, WebhookEventCreate

router = APIRouter(prefix='/integrations', tags=['Integrations'])

@router.post('/connections', response_model=ConnectionResponse, status_code=201)
def create_connection(payload: ConnectionCreate, db: Session = Depends(get_db)):
    if payload.provider.lower() not in {'salla', 'generic'}:
        raise HTTPException(400, 'Unsupported provider')
    obj = IntegrationConnection(**payload.model_dump(), provider=payload.provider.lower())
    db.add(obj)
    try:
        db.commit(); db.refresh(obj)
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(409, 'Integration connection already exists') from exc
    return obj

@router.get('/connections', response_model=list[ConnectionResponse])
def list_connections(company_id: int = Query(..., gt=0), db: Session = Depends(get_db)):
    return db.query(IntegrationConnection).filter(IntegrationConnection.company_id == company_id).order_by(IntegrationConnection.id.desc()).all()

@router.post('/salla/{connection_id}/webhook', status_code=202)
def receive_salla_webhook(connection_id: int, payload: WebhookEventCreate, db: Session = Depends(get_db)):
    connection = db.query(IntegrationConnection).filter(IntegrationConnection.id == connection_id, IntegrationConnection.provider == 'salla', IntegrationConnection.is_active.is_(True)).first()
    if not connection:
        raise HTTPException(404, 'Salla connection not found')
    existing = db.query(IntegrationEvent).filter(IntegrationEvent.connection_id == connection_id, IntegrationEvent.external_event_id == payload.external_event_id).first()
    if existing:
        return {'accepted': True, 'duplicate': True, 'event_id': existing.id}
    event = IntegrationEvent(company_id=connection.company_id, connection_id=connection_id, external_event_id=payload.external_event_id, event_type=payload.event_type, payload=json.dumps(payload.payload, ensure_ascii=False), status='received')
    db.add(event); connection.last_sync_at = datetime.now(timezone.utc)
    try:
        db.commit(); db.refresh(event)
    except IntegrityError:
        db.rollback(); return {'accepted': True, 'duplicate': True}
    return {'accepted': True, 'duplicate': False, 'event_id': event.id}

@router.get('/events', status_code=200)
def list_events(company_id: int = Query(..., gt=0), db: Session = Depends(get_db)):
    return db.query(IntegrationEvent).filter(IntegrationEvent.company_id == company_id).order_by(IntegrationEvent.id.desc()).limit(200).all()
