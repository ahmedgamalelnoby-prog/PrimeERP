from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import IntegrationConnection
from .salla_service import normalize_salla_event


SALLA_BASE_URL = "https://api.salla.dev/admin/v2"


class SallaSyncError(RuntimeError):
    pass


def _token(connection: IntegrationConnection) -> str:
    token = connection.credential_ref
    if not token:
        raise SallaSyncError("Salla connection has no access token reference")
    return token


def _data(response: dict[str, Any]) -> list[dict[str, Any]]:
    value = response.get("data")
    return value if isinstance(value, list) else []


def _pages(response: dict[str, Any]) -> tuple[int, int]:
    pagination = response.get("pagination") or {}
    return int(pagination.get("currentPage") or 1), int(pagination.get("totalPages") or 1)


def _request(client: httpx.Client, path: str, token: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    response = client.get(path, params=params, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
    if response.status_code >= 400:
        raise SallaSyncError(f"Salla API {response.status_code}: {response.text[:500]}")
    payload = response.json()
    if not isinstance(payload, dict):
        raise SallaSyncError("Salla API returned a non-object response")
    return payload


def _connection(db: Session, connection_id: int) -> IntegrationConnection:
    connection = db.scalar(select(IntegrationConnection).where(IntegrationConnection.id == connection_id, IntegrationConnection.provider == "salla", IntegrationConnection.is_active.is_(True)))
    if connection is None:
        raise SallaSyncError("Active Salla integration connection not found")
    return connection


def sync_collection(db: Session, connection_id: int, resource: str, event_type: str, *, from_date: str | None = None, to_date: str | None = None, timeout: float = 30.0) -> dict[str, int]:
    """Sequentially import a Salla collection through the existing event normalizer."""
    connection = _connection(db, connection_id)
    token = _token(connection)
    base_url = (connection.base_url or SALLA_BASE_URL).rstrip("/")
    imported = 0
    page = 1
    total_pages = 1
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        while page <= total_pages:
            params: dict[str, Any] = {"page": page, "per_page": 30}
            if from_date:
                params["from_date"] = from_date
            if to_date:
                params["to_date"] = to_date
            payload = _request(client, f"/{resource.lstrip('/')}", token, params)
            rows = _data(payload)
            current, total_pages = _pages(payload)
            if current != page:
                raise SallaSyncError(f"Salla returned page {current} while requesting {page}")
            for row in rows:
                if not isinstance(row, dict):
                    continue
                external_id = row.get("id")
                if external_id is None:
                    continue
                event = type("SyncEvent", (), {
                    "payload": row,
                    "event_type": event_type,
                    "company_id": connection.company_id,
                    "connection_id": connection.id,
                })()
                normalize_salla_event(db, event)  # type: ignore[arg-type]
                imported += 1
            db.commit()
            page += 1
    connection.last_sync_at = datetime.utcnow()
    db.commit()
    return {"imported": imported, "pages": total_pages}


def full_sync(db: Session, connection_id: int, *, from_date: str | None = None, to_date: str | None = None) -> dict[str, dict[str, int]]:
    """Import the core Salla datasets into PrimeERP without bypassing webhook normalization."""
    return {
        "orders": sync_collection(db, connection_id, "orders", "order.created", from_date=from_date, to_date=to_date),
        "products": sync_collection(db, connection_id, "products", "product.updated"),
        "customers": sync_collection(db, connection_id, "customers", "customer.updated"),
        "shipments": sync_collection(db, connection_id, "shipments", "shipment.updated"),
        "invoices": sync_collection(db, connection_id, "orders/invoices", "invoice.created", from_date=from_date, to_date=to_date),
    }
