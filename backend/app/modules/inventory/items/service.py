from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.accounting.models import TaxRate
from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.items.repository import inventory_item_repository
from app.modules.inventory.items.schemas import InventoryItemCreate, InventoryItemUpdate
from app.modules.saas.entitlements import enforce_product_limit
from app.modules.uom.models import UnitOfMeasure


class InventoryItemService:
    def list(self, db: Session, *, company_id: int, active_only: bool = True):
        return inventory_item_repository.list_items(
            db, company_id=company_id, active_only=active_only
        )

    def get(self, db: Session, *, company_id: int, item_id: int):
        return inventory_item_repository.get_item(
            db, company_id=company_id, item_id=item_id
        )

    def _resolve_uom(self, db: Session, *, company_id: int, uom_id: int | None, uom_code: str | None) -> UnitOfMeasure:
        if uom_id is not None:
            uom = db.scalar(
                select(UnitOfMeasure).where(
                    UnitOfMeasure.id == uom_id,
                    UnitOfMeasure.company_id == company_id,
                    UnitOfMeasure.is_active.is_(True),
                )
            )
            if uom is None:
                raise ValueError("UOM is not active or does not belong to this company")
            return uom

        if uom_code:
            uom = db.scalar(
                select(UnitOfMeasure).where(
                    UnitOfMeasure.company_id == company_id,
                    UnitOfMeasure.code == uom_code,
                    UnitOfMeasure.is_active.is_(True),
                )
            )
            if uom is not None:
                return uom

        raise ValueError("A valid active UOM is required for the inventory item")

    def _validate_tax_profile(self, db: Session, *, company_id: int, tax_ids: list[int], profile_name: str):
        if not tax_ids:
            return []
        taxes = list(
            db.scalars(
                select(TaxRate).where(
                    TaxRate.company_id == company_id,
                    TaxRate.id.in_(tax_ids),
                    TaxRate.is_active.is_(True),
                )
            ).all()
        )
        found = {tax.id: tax for tax in taxes}
        missing = [tax_id for tax_id in tax_ids if tax_id not in found]
        if missing:
            raise ValueError(f"{profile_name} contains inactive or invalid tax ids: {missing}")
        return [tax.id for tax in taxes]

    def _validate_tax_profiles(self, db: Session, *, company_id: int, sales_tax_ids: list[int], purchase_tax_ids: list[int]):
        return (
            self._validate_tax_profile(db, company_id=company_id, tax_ids=sales_tax_ids, profile_name="Sales tax profile"),
            self._validate_tax_profile(db, company_id=company_id, tax_ids=purchase_tax_ids, profile_name="Purchase tax profile"),
        )

    def create(self, db: Session, payload: InventoryItemCreate, *, tenant_id: int | None = None):
        if tenant_id is not None:
            enforce_product_limit(db, tenant_id, payload.company_id)

        uom = self._resolve_uom(
            db,
            company_id=payload.company_id,
            uom_id=payload.uom_id,
            uom_code=payload.uom,
        )
        sales_tax_ids, purchase_tax_ids = self._validate_tax_profiles(
            db,
            company_id=payload.company_id,
            sales_tax_ids=payload.sales_tax_ids,
            purchase_tax_ids=payload.purchase_tax_ids,
        )
        values = payload.model_dump()
        values["uom_id"] = uom.id
        values["uom"] = uom.code
        values["sales_tax_ids"] = sales_tax_ids
        values["purchase_tax_ids"] = purchase_tax_ids
        item = InventoryItem(**values)
        db.add(item)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("SKU or barcode already exists for this company") from exc
        db.refresh(item)
        return item

    def update(
        self,
        db: Session,
        *,
        company_id: int,
        item_id: int,
        payload: InventoryItemUpdate,
    ):
        item = self.get(db, company_id=company_id, item_id=item_id)
        if item is None:
            raise ValueError("Inventory item not found")

        values = payload.model_dump(exclude_unset=True)
        if "uom_id" in values or "uom" in values:
            uom = self._resolve_uom(
                db,
                company_id=company_id,
                uom_id=values.get("uom_id"),
                uom_code=values.get("uom"),
            )
            values["uom_id"] = uom.id
            values["uom"] = uom.code

        sales_tax_ids = values.get("sales_tax_ids", item.sales_tax_ids or [])
        purchase_tax_ids = values.get("purchase_tax_ids", item.purchase_tax_ids or [])
        if "sales_tax_ids" in values or "purchase_tax_ids" in values:
            sales_tax_ids, purchase_tax_ids = self._validate_tax_profiles(
                db,
                company_id=company_id,
                sales_tax_ids=sales_tax_ids,
                purchase_tax_ids=purchase_tax_ids,
            )
            values["sales_tax_ids"] = sales_tax_ids
            values["purchase_tax_ids"] = purchase_tax_ids

        for key, value in values.items():
            setattr(item, key, value)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("SKU or barcode already exists for this company") from exc
        db.refresh(item)
        return item

    def stock(self, db: Session, *, company_id: int, item_id: int | None = None):
        return inventory_item_repository.list_stock(
            db, company_id=company_id, item_id=item_id
        )


inventory_item_service = InventoryItemService()
