from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.catalog.models import ProductVariant
from app.modules.inventory.items.models import InventoryItem
from .models import IntegrationProductMapping
from .salla_models import SallaProduct, SallaProductVariant


def _first_text(*values: Any) -> str | None:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _url(value: Any) -> str | None:
    if isinstance(value, dict):
        return _first_text(value.get("url"), value.get("customer"), value.get("admin"), value.get("link"))
    return _first_text(value)


def _find_local_product(db: Session, company_id: int, salla: SallaProduct) -> InventoryItem | None:
    candidates = [salla.sku, salla.gtin]
    for value in candidates:
        key = _first_text(value)
        if not key:
            continue
        row = db.scalar(
            select(InventoryItem)
            .where(
                InventoryItem.company_id == company_id,
                InventoryItem.is_active.is_(True),
                (InventoryItem.sku == key) | (InventoryItem.barcode == key),
            )
            .with_for_update()
        )
        if row is not None:
            return row
    return None


def _find_local_variant(db: Session, company_id: int, product_id: int, salla: SallaProductVariant) -> ProductVariant | None:
    keys = [_first_text(salla.sku), _first_text(salla.gtin), _first_text(salla.barcode)]
    for key in keys:
        if not key:
            continue
        row = db.scalar(
            select(ProductVariant)
            .where(
                ProductVariant.company_id == company_id,
                ProductVariant.product_id == product_id,
                ProductVariant.is_active.is_(True),
                ProductVariant.sku == key,
            )
            .with_for_update()
        )
        if row is not None:
            return row
    return None


def _upsert_mapping(
    db: Session,
    *,
    company_id: int,
    connection_id: int,
    product_id: int,
    variant_id: int | None,
    external_id: str,
    external_sku: str | None,
    external_url: str | None,
) -> IntegrationProductMapping:
    mapping = db.scalar(
        select(IntegrationProductMapping)
        .where(
            IntegrationProductMapping.company_id == company_id,
            IntegrationProductMapping.connection_id == connection_id,
            IntegrationProductMapping.external_id == external_id,
        )
        .with_for_update()
    )
    if mapping is not None:
        if mapping.product_id != product_id or mapping.variant_id != variant_id:
            raise ValueError("Salla external product is already mapped to another ERP product or variant")
        mapping.external_sku = external_sku
        mapping.external_url = external_url
        mapping.sync_status = "active"
        return mapping

    mapping = IntegrationProductMapping(
        company_id=company_id,
        connection_id=connection_id,
        product_id=product_id,
        variant_id=variant_id,
        external_id=external_id,
        external_sku=external_sku,
        external_url=external_url,
        sync_direction="bidirectional",
        sync_status="active",
    )
    db.add(mapping)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Concurrent Salla mapping conflict; retry reconciliation") from exc
    return mapping


def reconcile_salla_product_mapping(
    db: Session,
    *,
    company_id: int,
    connection_id: int,
    salla_product_id: int,
) -> dict[str, int | str | None]:
    salla_product = db.scalar(
        select(SallaProduct)
        .where(SallaProduct.id == salla_product_id, SallaProduct.company_id == company_id, SallaProduct.connection_id == connection_id)
        .with_for_update()
    )
    if salla_product is None:
        raise ValueError("Salla product not found for this company and connection")

    local_product = _find_local_product(db, company_id, salla_product)
    if local_product is None:
        return {"product_mapped": 0, "variants_mapped": 0, "product_id": None, "reason": "no_matching_erp_product"}

    external_id = str(salla_product.external_id).strip()
    if not external_id:
        raise ValueError("Salla product has no external id")
    _upsert_mapping(
        db,
        company_id=company_id,
        connection_id=connection_id,
        product_id=local_product.id,
        variant_id=None,
        external_id=external_id,
        external_sku=_first_text(salla_product.sku),
        external_url=_url(salla_product.urls),
    )

    variants = list(
        db.scalars(
            select(SallaProductVariant)
            .where(SallaProductVariant.product_id == salla_product.id, SallaProductVariant.company_id == company_id, SallaProductVariant.connection_id == connection_id)
            .order_by(SallaProductVariant.id)
        ).all()
    )
    mapped = 0
    for salla_variant in variants:
        local_variant = _find_local_variant(db, company_id, local_product.id, salla_variant)
        if local_variant is None:
            continue
        variant_external_id = str(salla_variant.external_id).strip()
        if not variant_external_id:
            continue
        _upsert_mapping(
            db,
            company_id=company_id,
            connection_id=connection_id,
            product_id=local_product.id,
            variant_id=local_variant.id,
            external_id=variant_external_id,
            external_sku=_first_text(salla_variant.sku, salla_variant.barcode, salla_variant.gtin),
            external_url=None,
        )
        mapped += 1

    db.flush()
    return {"product_mapped": 1, "variants_mapped": mapped, "product_id": local_product.id, "reason": None}
