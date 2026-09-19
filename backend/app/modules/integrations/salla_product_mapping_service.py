from __future__ import annotations

from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.catalog.models import ProductBarcode, ProductVariant, Recipe
from app.modules.companies.models import Company
from app.modules.inventory.items.models import InventoryItem
from .models import IntegrationConnection, IntegrationProductMapping
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
    for value in (_first_text(salla.sku), _first_text(salla.gtin)):
        if not value:
            continue
        row = db.scalar(
            select(InventoryItem)
            .where(
                InventoryItem.company_id == company_id,
                InventoryItem.is_active.is_(True),
                or_(InventoryItem.sku == value, InventoryItem.barcode == value),
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
                or_(ProductVariant.sku == key, ProductVariant.name_ar == key, ProductVariant.name_en == key),
            )
            .with_for_update()
        )
        if row is not None:
            return row
        barcode_variant = db.scalar(
            select(ProductVariant)
            .join(ProductBarcode, ProductBarcode.variant_id == ProductVariant.id)
            .where(
                ProductVariant.company_id == company_id,
                ProductVariant.product_id == product_id,
                ProductVariant.is_active.is_(True),
                ProductBarcode.company_id == company_id,
                ProductBarcode.barcode == key,
                ProductBarcode.is_active.is_(True),
            )
            .with_for_update()
        )
        if barcode_variant is not None:
            return barcode_variant
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

    try:
        with db.begin_nested():
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
            db.flush()
    except IntegrityError as exc:
        existing = db.scalar(
            select(IntegrationProductMapping)
            .where(
                IntegrationProductMapping.company_id == company_id,
                IntegrationProductMapping.connection_id == connection_id,
                IntegrationProductMapping.external_id == external_id,
            )
            .with_for_update()
        )
        if existing is None:
            raise ValueError("Concurrent Salla mapping conflict; retry reconciliation") from exc
        if existing.product_id != product_id or existing.variant_id != variant_id:
            raise ValueError("Salla external product is already mapped to another ERP product or variant") from exc
        existing.external_sku = external_sku
        existing.external_url = external_url
        existing.sync_status = "active"
        mapping = existing
    return mapping


def reconcile_salla_product_mapping(
    db: Session,
    *,
    company_id: int,
    connection_id: int,
    salla_product_id: int,
) -> dict[str, int | str | None]:
    connection = db.scalar(
        select(IntegrationConnection)
        .join(Company, Company.id == IntegrationConnection.company_id)
        .where(
            IntegrationConnection.id == connection_id,
            IntegrationConnection.company_id == company_id,
            IntegrationConnection.provider == "salla",
            IntegrationConnection.is_active.is_(True),
            Company.id == company_id,
            Company.is_active.is_(True),
        )
    )
    if connection is None:
        raise ValueError("Salla connection not found or inactive")

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
    # Bind every recipe version for this commercial Product to the same external SKU.\n    # Recipe.code remains the ERP-internal code.\n    salla_sku = _first_text(salla_product.sku)\n    if salla_sku:\n        from app.modules.catalog.models import CatalogProduct\n        catalog_product = db.scalar(select(CatalogProduct).where(\n            CatalogProduct.company_id == company_id,\n            CatalogProduct.item_id == local_product.id,\n            CatalogProduct.is_active.is_(True),\n        ))\n        if catalog_product is not None:\n            recipes = db.scalars(select(Recipe).where(\n                Recipe.company_id == company_id,\n                Recipe.catalog_product_id == catalog_product.id,\n            ).with_for_update()).all()\n            for recipe in recipes:\n                recipe.external_sku = salla_sku\n
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
