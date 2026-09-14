from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.catalog.models import ProductBarcode, ProductVariant
from app.modules.inventory.items.models import InventoryItem
from app.modules.uom.models import UnitOfMeasure


class ProductVariantLifecycleService:
    """Mutation boundary for variant/barcode lifecycle operations.

    Variants and barcodes are deactivated rather than physically deleted so
    historical sales, inventory and external-channel mappings remain auditable.
    """

    def _variant(self, db: Session, company_id: int, variant_id: int) -> ProductVariant:
        row = db.scalar(select(ProductVariant).where(ProductVariant.id == variant_id, ProductVariant.company_id == company_id).with_for_update())
        if row is None:
            raise ValueError("Product variant not found")
        return row

    def _product(self, db: Session, company_id: int, product_id: int) -> InventoryItem:
        row = db.scalar(select(InventoryItem).where(InventoryItem.id == product_id, InventoryItem.company_id == company_id, InventoryItem.is_active.is_(True)))
        if row is None:
            raise ValueError("Product not found or inactive")
        return row

    def _uom(self, db: Session, company_id: int, uom_id: int | None) -> None:
        if uom_id is None:
            return
        if db.scalar(select(UnitOfMeasure.id).where(UnitOfMeasure.id == uom_id, UnitOfMeasure.company_id == company_id, UnitOfMeasure.is_active.is_(True))) is None:
            raise ValueError("Variant UOM does not belong to this company or is inactive")

    def update_variant(self, db: Session, company_id: int, variant_id: int, payload):
        variant = self._variant(db, company_id, variant_id)
        if not variant.is_active:
            raise ValueError("Cannot update an inactive variant")
        if payload.product_id != variant.product_id:
            raise ValueError("Variant product cannot be changed after creation")
        self._product(db, company_id, variant.product_id)
        self._uom(db, company_id, payload.uom_id)
        try:
            attributes = json.dumps(payload.attributes or {}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        except (TypeError, ValueError) as exc:
            raise ValueError("Variant attributes must be JSON serializable") from exc
        sku = payload.sku.strip()
        name_ar = payload.name_ar.strip()
        if not sku or not name_ar:
            raise ValueError("Variant SKU and Arabic name are required")
        duplicate = db.scalar(select(ProductVariant.id).where(ProductVariant.company_id == company_id, ProductVariant.sku == sku, ProductVariant.id != variant.id))
        if duplicate is not None:
            raise ValueError("Variant SKU already exists for this company")
        variant.sku = sku
        variant.name_ar = name_ar
        variant.name_en = payload.name_en.strip() if payload.name_en else None
        variant.attributes = attributes
        variant.uom_id = payload.uom_id
        variant.sales_price = payload.sales_price
        variant.purchase_price = payload.purchase_price
        db.commit()
        db.refresh(variant)
        return variant

    def deactivate_variant(self, db: Session, company_id: int, variant_id: int):
        variant = self._variant(db, company_id, variant_id)
        variant.is_active = False
        active_barcodes = db.scalars(select(ProductBarcode).where(ProductBarcode.company_id == company_id, ProductBarcode.variant_id == variant.id, ProductBarcode.is_active.is_(True)).with_for_update()).all()
        for barcode in active_barcodes:
            barcode.is_active = False
            barcode.is_primary = False
        db.commit()
        db.refresh(variant)
        return variant

    def reactivate_variant(self, db: Session, company_id: int, variant_id: int):
        variant = self._variant(db, company_id, variant_id)
        self._product(db, company_id, variant.product_id)
        self._uom(db, company_id, variant.uom_id)
        variant.is_active = True
        db.commit()
        db.refresh(variant)
        return variant

    def deactivate_barcode(self, db: Session, company_id: int, barcode_id: int):
        barcode = db.scalar(select(ProductBarcode).where(ProductBarcode.id == barcode_id, ProductBarcode.company_id == company_id).with_for_update())
        if barcode is None:
            raise ValueError("Barcode not found")
        barcode.is_active = False
        barcode.is_primary = False
        db.commit()
        db.refresh(barcode)
        return barcode

    def reactivate_barcode(self, db: Session, company_id: int, barcode_id: int):
        barcode = db.scalar(select(ProductBarcode).where(ProductBarcode.id == barcode_id, ProductBarcode.company_id == company_id).with_for_update())
        if barcode is None:
            raise ValueError("Barcode not found")
        if barcode.variant_id is not None:
            variant = self._variant(db, company_id, barcode.variant_id)
            if not variant.is_active:
                raise ValueError("Cannot reactivate a barcode for an inactive variant")
        self._product(db, company_id, barcode.product_id)
        duplicate = db.scalar(select(ProductBarcode.id).where(ProductBarcode.company_id == company_id, ProductBarcode.barcode == barcode.barcode, ProductBarcode.id != barcode.id, ProductBarcode.is_active.is_(True)))
        if duplicate is not None:
            raise ValueError("An active barcode with this value already exists for this company")
        barcode.is_active = True
        db.commit()
        db.refresh(barcode)
        return barcode


product_variant_lifecycle_service = ProductVariantLifecycleService()
