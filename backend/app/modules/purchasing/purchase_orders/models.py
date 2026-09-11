from sqlalchemy import CheckConstraint, Column, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from app.database.base import Base


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("purchasing_suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("inventory_warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    order_number = Column(String(50), nullable=False)
    order_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="draft", index=True)
    reference = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    total_amount = Column(Numeric(18, 4), nullable=False, default=0)

    supplier = relationship("Supplier")
    warehouse = relationship("InventoryWarehouse")
    lines = relationship("PurchaseOrderLine", back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("status IN ('draft','approved','partially_received','received','cancelled')", name="ck_purchase_order_status"),
        CheckConstraint("total_amount >= 0", name="ck_purchase_order_total"),
    )


class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"
    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_price = Column(Numeric(18, 4), nullable=False, default=0)
    received_quantity = Column(Numeric(18, 4), nullable=False, default=0)

    order = relationship("PurchaseOrder", back_populates="lines")
    item = relationship("InventoryItem")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_purchase_line_quantity"),
        CheckConstraint("unit_price >= 0", name="ck_purchase_line_unit_price"),
        CheckConstraint("received_quantity >= 0 AND received_quantity <= quantity", name="ck_purchase_line_received"),
    )
