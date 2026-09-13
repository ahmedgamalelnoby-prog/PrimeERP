from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import IntegrationConnection
from .salla_service import normalize_salla_event

SALLA_BASE_URL = "https://api.salla.dev/admin/v2"

class SallaSyncError(RuntimeError): pass

def _token(connection: IntegrationConnection) -> str:
    ref = connection.credential_ref
    if not ref: raise SallaSyncError("Salla access-token environment reference is not configured")
    token = os.getenv(ref)
    if not token: raise SallaSyncError(f"Salla access-token environment variable '{ref}' is unavailable")
    return token

def _data(response: dict[str, Any]) -> list[dict[str, Any]]:
    value = response.get("data"); return value if isinstance(value, list) else []

def _pages(response: dict[str, Any]) -> tuple[int, int]:
    pagination = response.get("pagination") or {}; return int(pagination.get("currentPage") or 1), int(pagination.get("totalPages") or 1)

def _request(client: requests.Session, path: str, token: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    response = client.get(path, params=params, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}, timeout=30)
    if response.status_code >= 400: raise SallaSyncError(f"Salla API {response.status_code}: {response.text[:500]}")
    payload = response.json()
    if not isinstance(payload, dict): raise SallaSyncError("Salla API returned a non-object response")
    return payload

def _connection(db: Session, connection_id: int) -> IntegrationConnection:
    connection = db.scalar(select(IntegrationConnection).where(IntegrationConnection.id == connection_id, IntegrationConnection.provider == "salla", IntegrationConnection.is_active.is_(True)))
    if connection is None: raise SallaSyncError("Active Salla integration connection not found")
    return connection

def _event(connection, payload, event_type):
    return type("SyncEvent", (), {"payload": payload, "event_type": event_type, "company_id": connection.company_id, "connection_id": connection.id})()

def _normalize(db, connection, payload, event_type):
    normalize_salla_event(db, _event(connection, payload, event_type))  # type: ignore[arg-type]

def _enrich_order(client, base_url: str, token: str, row: dict[str, Any]) -> dict[str, Any]:
    order_id = row.get("id")
    detail_payload = _request(client, f"{base_url}/orders/{order_id}", token, {"format": "light"})
    detail = detail_payload.get("data") if isinstance(detail_payload.get("data"), dict) else row
    if not isinstance(detail, dict): detail = row
    items_payload = _request(client, f"{base_url}/orders/items", token, {"order_id": order_id})
    items = _data(items_payload)
    if items: detail["items"] = items
    return detail

def sync_collection(db: Session, connection_id: int, resource: str, event_type: str, *, from_date: str | None = None, to_date: str | None = None) -> dict[str, int]:
    connection = _connection(db, connection_id); token = _token(connection); base_url = (connection.base_url or SALLA_BASE_URL).rstrip("/")
    imported = 0; enriched = 0; page = 1; total_pages = 1; client = requests.Session()
    try:
        while page <= total_pages:
            params: dict[str, Any] = {"page": page, "per_page": 30}
            if from_date: params["from_date"] = from_date
            if to_date: params["to_date"] = to_date
            payload = _request(client, f"{base_url}/{resource.lstrip('/')}", token, params)
            rows = _data(payload); current, total_pages = _pages(payload)
            if current != page: raise SallaSyncError(f"Salla returned page {current} while requesting {page}")
            for row in rows:
                if not isinstance(row, dict) or row.get("id") is None: continue
                normalized = row
                if resource == "orders":
                    normalized = _enrich_order(client, base_url, token, row); enriched += 1
                _normalize(db, connection, normalized, event_type); imported += 1
            db.commit(); page += 1
    finally: client.close()
    connection.last_sync_at = datetime.now(timezone.utc); db.commit()
    return {"imported": imported, "pages": total_pages, "enriched_orders": enriched}

def full_sync(db: Session, connection_id: int, *, from_date: str | None = None, to_date: str | None = None) -> dict[str, dict[str, int]]:
    return {
        "orders": sync_collection(db, connection_id, "orders", "order.created", from_date=from_date, to_date=to_date),
        "products": sync_collection(db, connection_id, "products", "product.updated"),
        "customers": sync_collection(db, connection_id, "customers", "customer.updated"),
        "shipments": sync_collection(db, connection_id, "shipments", "shipment.updated"),
        "invoices": sync_collection(db, connection_id, "orders/invoices", "invoice.created", from_date=from_date, to_date=to_date),
    }
