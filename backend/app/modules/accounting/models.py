from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Integer, Numeric, String
from app.database.base import Base


class TaxRate(Base):
    __tablename__ = "tax_rates"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(40), nullable=False)
    name = Column(String(120), nullable=False)
    rate = Column(Numeric(8, 4), nullable=False)
    tax_type = Column(String(20), nullable=False, server_default="vat")
    is_withholding = Column(Boolean, nullable=False, server_default="false")
    is_active = Column(Boolean, nullable=False, server_default="true")

    __table_args__ = (
        CheckConstraint("rate >= 0 AND rate <= 100", name="ck_tax_rate_bounds"),
    )
