from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, Text
from app.database.base import Base


class Supplier(Base):
    __tablename__ = "purchasing_suppliers"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    tax_id = Column(String(100), nullable=True)
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    is_active = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        CheckConstraint("length(trim(code)) > 0", name="ck_supplier_code"),
        CheckConstraint("length(trim(name)) > 0", name="ck_supplier_name"),
        CheckConstraint("is_active IN (0,1)", name="ck_supplier_active"),
    )
