from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.companies.models import Company
from app.modules.catalog.models import ProductVariant
from app.modules.inventory.items.models import InventoryItem
from .models import IntegrationConnection, IntegrationProductMapping

_ALLOWED_DIRECTIONS = {"inbound", "outbound", "bidirectional"}
_ALLOWED_STATUSES = {"active", "paused", "error", "archived"}


def _connection(db: Session, company_id: int, connection_id: int) -> IntegrationConnection:
    row = db.scalar(select(IntegrationConnection).join(Company, Company.id == IntegrationConnection.company_id).where(
        IntegrationConnection.id == connection_id, IntegrationConnection.company_id == company_id,
        IntegrationConnection.is_active.is_(True), Company.id == company_id, Company.is_active.is_(True)))
    if row is None:
        raise ValueError("Integration connection not found or inactive")
    return row


def _product(db: Session, company_id: int, product_id: int) -> InventoryItem:
    row = db.scalar(select(InventoryItem).where(InventoryItem.id == product_id, InventoryItem.company_id == company_id, InventoryItem.is_active.is_(True)))
    if row is None:
        raise ValueError("Product not found or inactive")
    return row


def _variant(db: Session, company_id: int, variant_id: int, product_id: int) -> ProductVariant:
    row = db.scalar(select(ProductVariant).where(ProductVariant.id == variant_id, ProductVariant.company_id == company_id, ProductVariant.product_id == product_id, ProductVariant.is_active.is_(True)))
    if row is None:
        raise ValueError("Variant not found, inactive, or does not belong to the product")
    return row


def create_mapping(db: Session, *, company_id: int, connection_id: int, product_id: int, variant_id: int | None,
                   external_id: str, external_sku: str | None = None, external_url: str | None = None,
                   sync_direction: str = "bidirectional"):
    _connection(db, company_id, connection_id)
    _product(db, company_id, product_id)
    if variant_id is not None:
        _variant(db, company_id, variant_id, product_id)
    external_id = external_id.strip()
    if not external_id:
        raise ValueError("External product id is required")
    sync_direction = sync_direction.strip().lower()
    if sync_direction not in _ALLOWED_DIRECTIONS:
        raise ValueError("Invalid sync direction")
    entity_type = "variant" if variant_id is not None else "product"
    mapping = IntegrationProductMapping(company_id=company_id, connection_id=connection_id,
                                        product_id=product_id, variant_id=variant_id, entity_type=entity_type,
                                        external_id=external_id,
                                        external_sku=external_sku.strip() if external_sku else None,
                                        external_url=external_url.strip() if external_url else None,
                                        sync_direction=sync_direction, sync_status="active")
    db.add(mapping)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("External id or local product/variant is already mapped for this connection and entity type") from exc
    db.refresh(mapping)
    return mapping


def list_mappings(db: Session, *, company_id: int, connection_id: int, product_id: int | None = None,
                  variant_id: int | None = None, status: str | None = None):
    _connection(db, company_id, connection_id)
    q = select(IntegrationProductMapping).where(IntegrationProductMapping.company_id == company_id,
                                                 IntegrationProductMapping.connection_id == connection_id)
    if product_id is not None: q = q.where(IntegrationProductMapping.product_id == product_id)
    if variant_id is not None: q = q.where(IntegrationProductMapping.variant_id == variant_id)
    if status is not None:
        status = status.strip().lower()
        if status not in _ALLOWED_STATUSES: raise ValueError("Invalid mapping status")
        q = q.where(IntegrationProductMapping.sync_status == status)
    return list(db.scalars(q.order_by(IntegrationProductMapping.id.desc())).all())


def find_by_external_id(db: Session, *, company_id: int, connection_id: int, external_id: str):
    _connection(db, company_id, connection_id)
    value = external_id.strip()
    if not value: raise ValueError("External product id is required")
    return list(db.scalars(select(IntegrationProductMapping).where(
        IntegrationProductMapping.company_id == company_id,
        IntegrationProductMapping.connection_id == connection_id,
        IntegrationProductMapping.external_id == value,
    ).order_by(IntegrationProductMapping.id.desc())).all())


def find_by_product(db: Session, *, company_id: int, connection_id: int, product_id: int, variant_id: int | None = None):
    _connection(db, company_id, connection_id); _product(db, company_id, product_id)
    q = select(IntegrationProductMapping).where(IntegrationProductMapping.company_id == company_id,
                                                  IntegrationProductMapping.connection_id == connection_id,
                                                  IntegrationProductMapping.product_id == product_id)
    if variant_id is not None:
        _variant(db, company_id, variant_id, product_id); q = q.where(IntegrationProductMapping.variant_id == variant_id)
    return list(db.scalars(q.order_by(IntegrationProductMapping.id.desc())).all())


def update_mapping(db: Session, *, company_id: int, mapping_id: int, external_id: str | None = None,
                   external_sku: str | None = None, external_url: str | None = None,
                   sync_direction: str | None = None, sync_status: str | None = None):
    mapping = db.scalar(select(IntegrationProductMapping).where(
        IntegrationProductMapping.id == mapping_id, IntegrationProductMapping.company_id == company_id).with_for_update())
    if mapping is None: raise ValueError("Product mapping not found")
    _connection(db, company_id, mapping.connection_id)
    if external_id is not None:
        mapping.external_id = external_id.strip()
        if not mapping.external_id: raise ValueError("External product id is required")
    if external_sku is not None: mapping.external_sku = external_sku.strip() or None
    if external_url is not None: mapping.external_url = external_url.strip() or None
    if sync_direction is not None:
        value = sync_direction.strip().lower()
        if value not in _ALLOWED_DIRECTIONS: raise ValueError("Invalid sync direction")
        mapping.sync_direction = value
    if sync_status is not None:
        value = sync_status.strip().lower()
        if value not in _ALLOWED_STATUSES: raise ValueError("Invalid mapping status")
        mapping.sync_status = value
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("External id or local product/variant is already mapped for this connection and entity type") from exc
    db.refresh(mapping)
    return mapping


def archive_mapping(db: Session, *, company_id: int, mapping_id: int):
    return update_mapping(db, company_id=company_id, mapping_id=mapping_id, sync_status="archived")


def mark_synced(db: Session, *, company_id: int, mapping_id: int):
    mapping = db.scalar(select(IntegrationProductMapping).where(
        IntegrationProductMapping.id == mapping_id, IntegrationProductMapping.company_id == company_id).with_for_update())
    if mapping is None: raise ValueError("Product mapping not found")
    mapping.last_synced_at = datetime.now(timezone.utc); mapping.sync_status = "active"
    db.commit(); db.refresh(mapping); return mapping
