from __future__ import annotations

from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.catalog.models import ProductBarcode, ProductVariant, Recipe, RecipeSkuMapping
from app.modules.companies.models import Company
from app.modules.inventory.items.models import InventoryItem
from .models import IntegrationConnection, IntegrationProductMapping
from app.modules.catalog.service import catalog_service
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

    external_id = str(salla_product.external_id).strip()
    if not external_id:
        raise ValueError("Salla product has no external id")

    # An explicit integration mapping is authoritative. SKU/GTIN matching is
    # only the discovery fallback, so an ERP SKU may legitimately differ from
    # the commerce-platform SKU.
    existing_mapping = db.scalar(
        select(IntegrationProductMapping)
        .where(
            IntegrationProductMapping.company_id == company_id,
            IntegrationProductMapping.connection_id == connection_id,
            IntegrationProductMapping.external_id == external_id,
            IntegrationProductMapping.variant_id.is_(None),
            IntegrationProductMapping.sync_status == "active",
        )
        .with_for_update()
    )
    if existing_mapping is not None:
        local_product = db.scalar(
            select(InventoryItem)
            .where(
                InventoryItem.id == existing_mapping.product_id,
                InventoryItem.company_id == company_id,
                InventoryItem.is_active.is_(True),
            )
            .with_for_update()
        )
    else:
        local_product = _find_local_product(db, company_id, salla_product)
    if local_product is None:
        return {"product_mapped": 0, "variants_mapped": 0, "product_id": None, "reason": "no_matching_erp_product"}

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
    # Every Salla SKU is a first-class recipe identity. Parent and variant SKUs
    # may point to the same recipe when their ERP composition is shared.
    # Recipe.code remains the ERP-internal code.
    salla_sku = _first_text(salla_product.sku)
    active_recipe = db.scalar(
        select(Recipe).where(
            Recipe.company_id == company_id,
            Recipe.product_id == local_product.id,
            Recipe.variant_id.is_(None),
            Recipe.is_active.is_(True),
        ).order_by(Recipe.version.desc()).limit(1)
    )
    if salla_sku:
        if active_recipe is None:
            raise ValueError("Salla product SKU requires an active ERP recipe before mapping")
        catalog_service.bind_recipe_sku(
            db, company_id, active_recipe.id, salla_sku,
            source="salla", external_id=external_id,
        )
        # Keep the legacy single-SKU field populated for backward compatibility.
        active_recipe.external_sku = salla_sku

    variants = list(
        db.scalars(
            select(SallaProductVariant).where(
                SallaProductVariant.product_id == salla_product.id,
                SallaProductVariant.company_id == company_id,
                SallaProductVariant.connection_id == connection_id,
            ).order_by(SallaProductVariant.id)
        ).all()
    )
    mapped = 0
    for salla_variant in variants:
        local_variant = _find_local_variant(db, company_id, local_product.id, salla_variant)
        variant_external_id = _first_text(salla_variant.external_id)
        variant_sku = _first_text(salla_variant.sku, salla_variant.barcode, salla_variant.gtin)
        if variant_sku and local_variant is None:
            raise ValueError("Salla variant SKU requires a matching ERP product variant before mapping")
        if variant_sku and not variant_external_id:
            raise ValueError("Salla variant SKU requires an external variant identity before mapping")
        if local_variant is None or not variant_external_id:
            continue
        _upsert_mapping(
            db,
            company_id=company_id,
            connection_id=connection_id,
            product_id=local_product.id,
            variant_id=local_variant.id,
            external_id=variant_external_id,
            external_sku=variant_sku,
            external_url=None,
        )
        if variant_sku:
            variant_recipe = db.scalar(
                select(Recipe).where(
                    Recipe.company_id == company_id,
                    Recipe.product_id == local_product.id,
                    Recipe.variant_id == local_variant.id,
                    Recipe.is_active.is_(True),
                ).order_by(Recipe.version.desc()).limit(1)
            ) or active_recipe
            if variant_recipe is None:
                raise ValueError("Salla variant SKU requires an active ERP recipe before mapping")
            catalog_service.bind_recipe_sku(
                db, company_id, variant_recipe.id, variant_sku,
                variant_id=local_variant.id, source="salla", external_id=variant_external_id,
            )
        mapped += 1

    db.flush()
    return {"product_mapped": 1, "variants_mapped": mapped, "product_id": local_product.id, "reason": None}

