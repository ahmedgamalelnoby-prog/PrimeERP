from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.modules.catalog.bundle_models import ProductBundle, ProductBundleLine
from app.modules.inventory.items.models import InventoryItem, InventoryStock
from app.modules.inventory.warehouses.models import InventoryWarehouse

class ProductBundleService:
    def _product(self, db: Session, company_id: int, product_id: int):
        row = db.scalar(select(InventoryItem).where(InventoryItem.id == product_id, InventoryItem.company_id == company_id, InventoryItem.is_active.is_(True)))
        if row is None: raise ValueError("Product not found or inactive")
        return row
    def _bundle(self, db: Session, company_id: int, bundle_id: int):
        row = db.scalar(select(ProductBundle).options(selectinload(ProductBundle.lines)).where(ProductBundle.id == bundle_id, ProductBundle.company_id == company_id))
        if row is None: raise ValueError("Product bundle not found")
        return row
    def create(self, db: Session, company_id: int, payload):
        product = self._product(db, company_id, payload.product_id)
        if any(x.component_product_id == product.id for x in payload.lines): raise ValueError("A bundle cannot contain itself")
        ids = [x.component_product_id for x in payload.lines]
        if len(ids) != len(set(ids)): raise ValueError("Duplicate bundle components are not allowed")
        components = list(db.scalars(select(InventoryItem).where(InventoryItem.company_id == company_id, InventoryItem.id.in_(ids), InventoryItem.is_active.is_(True))).all())
        if len(components) != len(ids): raise ValueError("One or more bundle components are invalid or inactive")
        bundle = ProductBundle(company_id=company_id, product_id=product.id, code=payload.code.strip(), name_ar=payload.name_ar.strip(), name_en=payload.name_en.strip() if payload.name_en else None, is_active=True)
        if not bundle.code or not bundle.name_ar: raise ValueError("Bundle code and Arabic name are required")
        for no, line in enumerate(payload.lines, 1): bundle.lines.append(ProductBundleLine(line_no=no, component_product_id=line.component_product_id, quantity=line.quantity))
        db.add(bundle)
        try: db.commit()
        except Exception as exc:
            db.rollback(); raise ValueError("Bundle code or product already has a bundle") from exc
        return self._bundle(db, company_id, bundle.id)
    def get(self, db: Session, company_id: int, bundle_id: int): return self._bundle(db, company_id, bundle_id)
    def list(self, db: Session, company_id: int, active_only: bool = True):
        q = select(ProductBundle).options(selectinload(ProductBundle.lines)).where(ProductBundle.company_id == company_id)
        if active_only: q = q.where(ProductBundle.is_active.is_(True))
        return list(db.scalars(q.order_by(ProductBundle.code)).all())
    def deactivate(self, db: Session, company_id: int, bundle_id: int):
        bundle = self._bundle(db, company_id, bundle_id); bundle.is_active = False; db.commit(); return bundle
    def reactivate(self, db: Session, company_id: int, bundle_id: int):
        bundle = self._bundle(db, company_id, bundle_id); self._product(db, company_id, bundle.product_id)
        for line in bundle.lines: self._product(db, company_id, line.component_product_id)
        bundle.is_active = True; db.commit(); return bundle
    def availability(self, db: Session, company_id: int, bundle_id: int, warehouse_id: int | None = None):
        bundle = self._bundle(db, company_id, bundle_id)
        if not bundle.is_active: raise ValueError("Bundle is inactive")
        if warehouse_id is not None and db.scalar(select(InventoryWarehouse.id).where(InventoryWarehouse.id == warehouse_id, InventoryWarehouse.company_id == company_id, InventoryWarehouse.is_active.is_(True))) is None:
            raise ValueError("Warehouse does not belong to this company or is inactive")
        result = []
        for line in bundle.lines:
            q = select(InventoryStock).where(InventoryStock.company_id == company_id, InventoryStock.item_id == line.component_product_id)
            if warehouse_id is not None: q = q.where(InventoryStock.warehouse_id == warehouse_id)
            stocks = list(db.scalars(q).all())
            available = sum((s.quantity_on_hand - s.quantity_reserved for s in stocks), 0)
            result.append({"component_product_id": line.component_product_id, "required_per_bundle": line.quantity, "available_quantity": available, "max_bundles": int(available / line.quantity)})
        return {"bundle_id": bundle.id, "product_id": bundle.product_id, "warehouse_id": warehouse_id, "max_available_bundles": min((x["max_bundles"] for x in result), default=0), "components": result}

product_bundle_service = ProductBundleService()
