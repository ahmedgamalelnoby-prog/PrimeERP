import json
from collections.abc import Mapping
from typing import Any

from sqlalchemy.orm import Session

from app.modules.audit.models import AuditEvent


_SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "credential",
    "credentials",
    "api_key",
    "authorization",
}


def _redact(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]" if str(key).lower() in _SENSITIVE_KEYS else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]
    return value


def record_audit_event(
    db: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: int | str | None = None,
    user_id: int | None = None,
    tenant_id: int | None = None,
    company_id: int | None = None,
    branch_id: int | None = None,
    request_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        user_id=user_id,
        tenant_id=tenant_id,
        company_id=company_id,
        branch_id=branch_id,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        action=action,
        request_id=request_id,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata_json=json.dumps(_redact(metadata or {}), ensure_ascii=False, default=str),
    )
    db.add(event)
    return event
