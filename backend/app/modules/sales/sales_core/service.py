from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.inventory.warehouses.models import InventoryWarehouse
from app.modules.platform.customers.models import Customer
from app.modules.sales.sales_core.models import SalesOrder


class SalesOrderService:
    def list(self, db: Session, company_id: int):
        return list(db.scalars(select(SalesOrder).where(SalesOrder.company_id == company_id).order_by(SalesOrder.id.desc())).all())

    def get(self, db: Session, company_id: int, order_id: int):
        return db.scalar(select(SalesOrder).where(SalesOrder.company_id == company_id, SalesOrder.id == order_id))

    def create(self, db: Session, payload):
        customer = db.scalar(select(Customer).where(Customer.id == payload.customer_id, Customer.company_id == payload.company_id, Customer.is_active.is_(True)))
        if customer is None:
            raise ValueError("Customer does not belong to the company or is inactive")
        warehouse = db.scalar(select(InventoryWarehouse).where(InventoryWarehouse.id == payload.warehouse_id, InventoryWarehouse.company_id == payload.company_id, InventoryWarehouse.is_active.is_(True)))
        if warehouse is None:
            raise ValueError("Warehouse does not belong to the company or is inactive")
        duplicate = db.scalar(select(SalesOrder).where(SalesOrder.company_id == payload.company_id, SalesOrder.order_number == payload.order_number))
        if duplicate:
            raise ValueError("Sales order number already exists for this company")
        order = SalesOrder(**payload.model_dump())
        db.add(order)
        db.flush()
        return order

    def confirm(self, db: Session, company_id: int, order_id: int):
        order = db.scalar(select(SalesOrder).where(SalesOrder.company_id == company_id, SalesOrder.id == order_id).with_for_update())
        if order is None:
            raise ValueError("Sales order not found")
        if order.status != "draft":
            raise ValueError("Only draft sales orders can be confirmed")
        order.status = "confirmed"
        db.flush()
        return order

    def cancel(self, db: Session, company_id: int, order_id: int):
        order = db.scalar(select(SalesOrder).where(SalesOrder.company_id == company_id, SalesOrder.id == order_id).with_for_update())
        if order is None:
            raise ValueError("Sales order not found")
        if order.status in {"shipped", "cancelled"}:
            raise ValueError("Sales order cannot be cancelled in its current state")
        order.status = "cancelled"
        db.flush()
        return order


sales_order_service = SalesOrderService()
