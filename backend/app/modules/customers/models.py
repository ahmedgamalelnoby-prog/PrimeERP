from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, TIMESTAMP, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False, index=True)
    customer_type = Column(String(30), nullable=False, default="customer", server_default="customer")
    phone = Column(String(50), nullable=True)
    email = Column(String(150), nullable=True)
    tax_id = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    credit_limit = Column(Integer, nullable=False, default=0, server_default="0")
    is_active = Column(Boolean, nullable=False, default=True, server_default="true", index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_customers_tenant_code"),)
