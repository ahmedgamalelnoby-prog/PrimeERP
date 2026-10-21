from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.warehouses.models import InventoryWarehouse
from app.modules.purchasing.suppliers.models import Supplier
from app.modules.purchasing.purchase_orders.models import PurchaseOrder, PurchaseOrderLine


class PurchaseOrderService:
    def list(self, db: Session, company_id: int):
        return list(db.scalars(select(PurchaseOrder).where(PurchaseOrder.company_id == company_id).order_by(PurchaseOrder.id.desc())).all())

    def get(self, db: Session, company_id: int, order_id: int):
        return db.scalar(select(PurchaseOrder).where(PurchaseOrder.company_id == company_id, PurchaseOrder.id == order_id))

    def create(self, db: Session, payload):
        supplier = db.scalar(select(Supplier).where(Supplier.id == payload.supplier_id, Supplier.company_id == payload.company_id, Supplier.is_active == 1))
        if supplier is None:
            raise ValueError("Supplier does not belong to the company or is inactive")
        warehouse = db.scalar(select(InventoryWarehouse).where(InventoryWarehouse.id == payload.warehouse_id, InventoryWarehouse.company_id == payload.company_id, InventoryWarehouse.is_active.is_(True)))
        if warehouse is None:
            raise ValueError("Warehouse does not belong to the company or is inactive")
        order = PurchaseOrder(company_id=payload.company_id, supplier_id=payload.supplier_id, warehouse_id=payload.warehouse_id, order_number=payload.order_number, order_date=payload.order_date, reference=payload.reference, notes=payload.notes, total_amount=0)
        total = Decimal("0")
        for line in payload.lines:
            item = db.scalar(select(InventoryItem).where(InventoryItem.id == line.item_id, InventoryItem.company_id == payload.company_id, InventoryItem.is_active.is_(True)))
            if item is None:
                raise ValueError(f"Item {line.item_id} does not belong to the company or is inactive")
            total += line.quantity * line.unit_price
            order.lines.append(PurchaseOrderLine(item_id=line.item_id, quantity=line.quantity, unit_price=line.unit_price))
        order.total_amount = total
        db.add(order)
        db.flush()
        return order

    def approve(self, db: Session, company_id: int, order_id: int):
        order = self._locked(db, company_id, order_id)
        if order.status != "draft":
            raise ValueError("Only draft purchase orders can be approved")
        if not order.lines:
            raise ValueError("Purchase order must contain at least one line")
        order.status = "approved"
        db.flush()
        return order

    def cancel(self, db: Session, company_id: int, order_id: int):
        order = self._locked(db, company_id, order_id)
        if order.status in ("received", "cancelled"):
            raise ValueError("Purchase order cannot be cancelled in its current state")
        order.status = "cancelled"
        db.flush()
        return order

    def _locked(self, db: Session, company_id: int, order_id: int):
        order = db.scalar(select(PurchaseOrder).where(PurchaseOrder.company_id == company_id, PurchaseOrder.id == order_id).with_for_update())
        if order is None:
            raise ValueError("Purchase order not found")
        return order


purchase_order_service = PurchaseOrderService()
