import json

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .models import AuditEvent

router = APIRouter(prefix="/audit", tags=["Audit"], dependencies=[Depends(require_permission("audit.access"))])


@router.get("/events")
def list_audit_events(
    company_id: int | None = Query(default=None, gt=0),
    entity_type: str | None = Query(default=None, max_length=80),
    entity_id: str | None = Query(default=None, max_length=80),
    action: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.tenant_id is None and not current_user.is_platform_admin:
        raise HTTPException(403, "User is not assigned to a tenant")
    stmt = select(AuditEvent)
    if not current_user.is_platform_admin:
        stmt = stmt.where(AuditEvent.tenant_id == current_user.tenant_id)
    if company_id is not None:
        stmt = stmt.where(AuditEvent.company_id == company_id)
    if entity_type:
        stmt = stmt.where(AuditEvent.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditEvent.entity_id == entity_id)
    if action:
        stmt = stmt.where(AuditEvent.action == action)
    rows = db.scalars(stmt.order_by(AuditEvent.id.desc()).limit(limit)).all()
    return [
        {
            "id": row.id,
            "user_id": row.user_id,
            "tenant_id": row.tenant_id,
            "company_id": row.company_id,
            "branch_id": row.branch_id,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "action": row.action,
            "request_id": row.request_id,
            "ip_address": row.ip_address,
            "user_agent": row.user_agent,
            "metadata": json.loads(row.metadata_json or "{}"),
            "created_at": row.created_at,
        }
        for row in rows
    ]
