from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database.base import Base


class InventoryWarehouse(Base):
    __tablename__ = "inventory_warehouses"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=True, index=True)
    code = Column(String(30), nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    is_central = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    company = relationship("Company")
    branch = relationship("Branch")
    stocks = relationship("InventoryStock", back_populates="warehouse")

    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_inventory_warehouse_company_code"),
        Index("uq_inventory_warehouse_one_central", "company_id", unique=True, postgresql_where=(is_central.is_(True))),
        CheckConstraint("(is_central = true AND branch_id IS NULL) OR (is_central = false AND branch_id IS NOT NULL)", name="ck_inventory_warehouse_scope"),
    )
