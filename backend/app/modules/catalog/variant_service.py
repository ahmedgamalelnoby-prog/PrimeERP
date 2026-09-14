from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.catalog.models import ProductBarcode, ProductVariant
from app.modules.inventory.items.models import InventoryItem
from app.modules.uom.models import UnitOfMeasure


class ProductVariantService:
    def _product(self, db: Session, company_id: int, product_id: int) -> InventoryItem:
        product = db.scalar(
            select(InventoryItem).where(
                InventoryItem.id == product_id,
                InventoryItem.company_id == company_id,
                InventoryItem.is_active.is_(True),
            )
        )
        if product is None:
            raise ValueError("Product not found or inactive")
        return product

    def _variant(self, db: Session, company_id: int, variant_id: int) -> ProductVariant:
        variant = db.scalar(
            select(ProductVariant).where(
                ProductVariant.id == variant_id,
                ProductVariant.company_id == company_id,
            )
        )
        if variant is None:
            raise ValueError("Product variant not found")
        return variant

    def _validate_uom(self, db: Session, company_id: int, uom_id: int | None) -> None:
        if uom_id is None:
            return
        if db.scalar(
            select(UnitOfMeasure.id).where(
                UnitOfMeasure.id == uom_id,
                UnitOfMeasure.company_id == company_id,
                UnitOfMeasure.is_active.is_(True),
            )
        ) is None:
            raise ValueError("Variant UOM does not belong to this company or is inactive")

    def create_variant(self, db: Session, company_id: int, payload):
        self._product(db, company_id, payload.product_id)
        self._validate_uom(db, company_id, payload.uom_id)
        try:
            attributes = json.dumps(payload.attributes or {}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        except (TypeError, ValueError) as exc:
            raise ValueError("Variant attributes must be JSON serializable") from exc
        variant = ProductVariant(
            company_id=company_id,
            product_id=payload.product_id,
            sku=payload.sku.strip(),
            name_ar=payload.name_ar.strip(),
            name_en=payload.name_en.strip() if payload.name_en else None,
            attributes=attributes,
            uom_id=payload.uom_id,
            sales_price=payload.sales_price,
            purchase_price=payload.purchase_price,
            is_active=True,
        )
        if not variant.sku:
            raise ValueError("Variant SKU is required")
        db.add(variant)
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            raise ValueError("Variant SKU already exists for this company") from exc
        db.refresh(variant)
        return variant

    def list_variants(self, db: Session, company_id: int, product_id: int | None = None):
        if product_id is not None:
            self._product(db, company_id, product_id)
        query = select(ProductVariant).where(ProductVariant.company_id == company_id)
        if product_id is not None:
            query = query.where(ProductVariant.product_id == product_id)
        return list(db.scalars(query.options(selectinload(ProductVariant.barcodes)).order_by(ProductVariant.product_id, ProductVariant.id)).all())

    def get_variant(self, db: Session, company_id: int, variant_id: int):
        variant = db.scalar(
            select(ProductVariant)
            .options(selectinload(ProductVariant.barcodes))
            .where(ProductVariant.id == variant_id, ProductVariant.company_id == company_id)
        )
        if variant is None:
            raise ValueError("Product variant not found")
        return variant

    def add_barcode(self, db: Session, company_id: int, variant_id: int, payload):
        variant = self._variant(db, company_id, variant_id)
        if not variant.is_active:
            raise ValueError("Cannot add a barcode to an inactive variant")
        product = self._product(db, company_id, variant.product_id)
        if payload.variant_id is not None and payload.variant_id != variant.id:
            raise ValueError("Barcode variant does not match the target variant")
        barcode = payload.barcode.strip()
        if not barcode:
            raise ValueError("Barcode is required")
        if db.scalar(
            select(ProductBarcode.id).where(
                ProductBarcode.company_id == company_id,
                ProductBarcode.barcode == barcode,
                ProductBarcode.is_active.is_(True),
            )
        ) is not None:
            raise ValueError("Barcode already exists for this company")
        if payload.is_primary:
            existing = db.scalars(
                select(ProductBarcode)
                .where(
                    ProductBarcode.company_id == company_id,
                    ProductBarcode.product_id == product.id,
                    ProductBarcode.is_primary.is_(True),
                    ProductBarcode.is_active.is_(True),
                )
                .with_for_update()
            ).all()
            for row in existing:
                row.is_primary = False
        row = ProductBarcode(
            company_id=company_id,
            product_id=product.id,
            variant_id=variant.id,
            barcode=barcode,
            barcode_type=payload.barcode_type.strip().upper(),
            is_primary=payload.is_primary,
            is_active=True,
        )
        db.add(row)
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            raise ValueError("Barcode already exists or is invalid") from exc
        db.refresh(row)
        return row

    def list_barcodes(self, db: Session, company_id: int, product_id: int | None = None, variant_id: int | None = None):
        if variant_id is not None:
            variant = self._variant(db, company_id, variant_id)
            if product_id is not None and variant.product_id != product_id:
                raise ValueError("Variant does not belong to the requested product")
            product_id = variant.product_id
        elif product_id is not None:
            self._product(db, company_id, product_id)
        query = select(ProductBarcode).where(ProductBarcode.company_id == company_id)
        if product_id is not None:
            query = query.where(ProductBarcode.product_id == product_id)
        if variant_id is not None:
            query = query.where(ProductBarcode.variant_id == variant_id)
        return list(db.scalars(query.order_by(ProductBarcode.product_id, ProductBarcode.id)).all())


product_variant_service = ProductVariantService()
