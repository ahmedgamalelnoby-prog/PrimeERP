from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import IntegrationConnection
from .salla_public_app_service import get_salla_access_token, SallaPublicAppError
from .salla_service import normalize_salla_event
from .salla_models import SallaShipment
from .salla_shipping_service import sync_salla_shipment

SALLA_BASE_URL = "https://api.salla.dev/admin/v2"

class SallaSyncError(RuntimeError): pass

def _token(db: Session, connection: IntegrationConnection) -> str:
    try:
        return get_salla_access_token(db, connection)
    except SallaPublicAppError:
        ref = connection.credential_ref
        if not ref:
            raise SallaSyncError("Salla access token is not configured")
        token = os.getenv(ref)
        if not token:
            raise SallaSyncError(f"Salla access-token environment variable '{ref}' is unavailable")
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

def sync_salla_shipping_companies(db: Session, connection_id: int) -> dict[str, int]:
    """Link Salla's active shipping companies to existing ERP carriers.

    The Salla company/courier id is the durable identity. Carrier names are
    used only once as a bootstrap match; after that the IntegrationMapping
    controls the relationship and prevents duplicate carriers.
    """
    connection = _connection(db, connection_id)
    token = _token(db, connection)
    base_url = (connection.base_url or SALLA_BASE_URL).rstrip("/")
    client = requests.Session()
    try:
        payload = _request(client, f"{base_url}/shipping/companies/", token)
    finally:
        client.close()
    rows = _data(payload)
    linked = 0
    unmatched = 0
    from sqlalchemy import func
    from app.modules.integrations.models import IntegrationMapping
    from app.modules.shipping.models import ShippingCarrier

    for row in rows:
        if not isinstance(row, dict) or row.get("id") is None:
            continue
        external_id = str(row["id"])
        mapping = db.scalar(select(IntegrationMapping).where(
            IntegrationMapping.company_id == connection.company_id,
            IntegrationMapping.connection_id == connection.id,
            IntegrationMapping.entity_type == "salla_shipping_company",
            IntegrationMapping.external_id == external_id,
        ))
        if mapping:
            carrier = db.scalar(select(ShippingCarrier).where(
                ShippingCarrier.id == mapping.local_id,
                ShippingCarrier.company_id == connection.company_id,
                ShippingCarrier.is_active.is_(True),
            ))
            if carrier:
                linked += 1
                continue

        name = str(row.get("name") or "").strip()
        carrier = None
        if name:
            carrier = db.scalar(select(ShippingCarrier).where(
                ShippingCarrier.company_id == connection.company_id,
                ShippingCarrier.is_active.is_(True),
                func.lower(func.trim(ShippingCarrier.name)) == name.lower(),
            ).order_by(ShippingCarrier.id))
        slug = str(row.get("slug") or "").strip().lower()
        if carrier is None and slug:
            carrier = db.scalar(select(ShippingCarrier).where(
                ShippingCarrier.company_id == connection.company_id,
                ShippingCarrier.is_active.is_(True),
                func.lower(ShippingCarrier.code).in_((slug, f"salla-{slug}")),
            ).order_by(ShippingCarrier.id))
        if carrier is None:
            unmatched += 1
            continue

        if mapping:
            mapping.local_id = carrier.id
        else:
            db.add(IntegrationMapping(
                company_id=connection.company_id,
                connection_id=connection.id,
                entity_type="salla_shipping_company",
                external_id=external_id,
                local_id=carrier.id,
            ))
        linked += 1

    db.commit()
    return {"salla_companies": len(rows), "linked": linked, "unmatched": unmatched}


def sync_collection(db: Session, connection_id: int, resource: str, event_type: str, *, from_date: str | None = None, to_date: str | None = None) -> dict[str, int]:
    connection = _connection(db, connection_id); token = _token(db, connection); base_url = (connection.base_url or SALLA_BASE_URL).rstrip("/")
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
                _normalize(db, connection, normalized, event_type)
                if resource == "shipments":
                    shipment = db.scalar(select(SallaShipment).where(
                        SallaShipment.company_id == connection.company_id,
                        SallaShipment.connection_id == connection.id,
                        SallaShipment.external_id == str(row.get("id")),
                    ))
                    if shipment is not None:
                        sync_salla_shipment(db, shipment)
                imported += 1
            db.commit(); page += 1
    finally: client.close()
    connection.last_sync_at = datetime.now(timezone.utc); db.commit()
    return {"imported": imported, "pages": total_pages, "enriched_orders": enriched}

def full_sync(db: Session, connection_id: int, *, from_date: str | None = None, to_date: str | None = None) -> dict[str, dict[str, int]]:
    shipping_companies = sync_salla_shipping_companies(db, connection_id)
    return {
        "orders": sync_collection(db, connection_id, "orders", "order.created", from_date=from_date, to_date=to_date),
        "products": sync_collection(db, connection_id, "products", "product.updated"),
        "customers": sync_collection(db, connection_id, "customers", "customer.updated"),
        "shipping_companies": shipping_companies,
        "shipments": sync_collection(db, connection_id, "shipments", "shipment.updated"),
        "invoices": sync_collection(db, connection_id, "orders/invoices", "invoice.created", from_date=from_date, to_date=to_date),
    }
