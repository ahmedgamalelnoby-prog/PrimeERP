from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.warehouses.models import InventoryWarehouse
from app.modules.platform.customers.models import Customer
from app.modules.sales.sales_core.models import SalesOrder, SalesOrderLine


class SalesOrderService:
    def list(self, db: Session, company_id: int):
        return list(db.scalars(
            select(SalesOrder)
            .options(selectinload(SalesOrder.lines))
            .where(SalesOrder.company_id == company_id)
            .order_by(SalesOrder.id.desc())
        ).unique().all())

    def get(self, db: Session, company_id: int, order_id: int):
        return db.scalar(
            select(SalesOrder)
            .options(selectinload(SalesOrder.lines))
            .where(SalesOrder.company_id == company_id, SalesOrder.id == order_id)
        )

    def create(self, db: Session, payload):
        customer = db.scalar(select(Customer).where(
            Customer.id == payload.customer_id,
            Customer.company_id == payload.company_id,
            Customer.is_active.is_(True),
        ))
        if customer is None:
            raise ValueError("Customer does not belong to the company or is inactive")
        warehouse = db.scalar(select(InventoryWarehouse).where(
            InventoryWarehouse.id == payload.warehouse_id,
            InventoryWarehouse.company_id == payload.company_id,
            InventoryWarehouse.is_active.is_(True),
        ))
        if warehouse is None:
            raise ValueError("Warehouse does not belong to the company or is inactive")
        duplicate = db.scalar(select(SalesOrder).where(
            SalesOrder.company_id == payload.company_id,
            SalesOrder.order_number == payload.order_number,
        ))
        if duplicate:
            raise ValueError("Sales order number already exists for this company")

        item_ids = {line.item_id for line in payload.lines}
        items = list(db.scalars(select(InventoryItem).where(
            InventoryItem.company_id == payload.company_id,
            InventoryItem.id.in_(item_ids),
            InventoryItem.is_active.is_(True),
        )).all())
        item_map = {item.id: item for item in items}
        if len(item_map) != len(item_ids):
            raise ValueError("One or more items do not belong to the company or are inactive")

        order = SalesOrder(
            company_id=payload.company_id,
            customer_id=payload.customer_id,
            warehouse_id=payload.warehouse_id,
            order_number=payload.order_number,
            order_date=payload.order_date,
            reference=payload.reference,
            notes=payload.notes,
            total_amount=Decimal("0"),
        )
        db.add(order)
        db.flush()

        total = Decimal("0")
        for line in payload.lines:
            gross = line.quantity * line.unit_price
            if line.discount_amount > gross:
                raise ValueError("Discount cannot exceed the line gross amount")
            line_total = gross - line.discount_amount
            db.add(SalesOrderLine(
                order_id=order.id,
                item_id=line.item_id,
                quantity=line.quantity,
                unit_price=line.unit_price,
                discount_amount=line.discount_amount,
                line_total=line_total,
            ))
            total += line_total
        order.total_amount = total
        db.flush()
        return order

    def confirm(self, db: Session, company_id: int, order_id: int):
        order = db.scalar(select(SalesOrder).where(
            SalesOrder.company_id == company_id,
            SalesOrder.id == order_id,
        ).options(selectinload(SalesOrder.lines)).with_for_update())
        if order is None:
            raise ValueError("Sales order not found")
        if order.status != "draft":
            raise ValueError("Only draft sales orders can be confirmed")
        if not order.lines:
            raise ValueError("Sales order must contain at least one line")
        order.status = "confirmed"
        db.flush()
        return order

    def cancel(self, db: Session, company_id: int, order_id: int):
        order = db.scalar(select(SalesOrder).where(
            SalesOrder.company_id == company_id,
            SalesOrder.id == order_id,
        ).with_for_update())
        if order is None:
            raise ValueError("Sales order not found")
        if order.status in {"shipped", "cancelled"}:
            raise ValueError("Sales order cannot be cancelled in its current state")
        order.status = "cancelled"
        db.flush()
        return order


sales_order_service = SalesOrderService()
