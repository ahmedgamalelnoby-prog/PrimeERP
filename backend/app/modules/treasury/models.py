from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, Index
from app.database.base import Base


class PaymentMethod(Base):
    __tablename__ = "treasury_payment_methods"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(30), nullable=False)
    name = Column(String(120), nullable=False)
    method_type = Column(String(30), nullable=False)
    is_incoming = Column(Integer, nullable=False, default=1)
    is_outgoing = Column(Integer, nullable=False, default=1)
    is_active = Column(Integer, nullable=False, default=1)
    __table_args__ = (Index("uq_treasury_payment_method_company_code", "company_id", "code", unique=True),)


class TreasuryPayment(Base):
    __tablename__ = "treasury_payments"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="RESTRICT"), nullable=True, index=True)
    payment_method_id = Column(Integer, ForeignKey("treasury_payment_methods.id", ondelete="RESTRICT"), nullable=False)
    party_type = Column(String(20), nullable=False)
    party_id = Column(Integer, nullable=False)
    direction = Column(String(10), nullable=False)
    payment_date = Column(Date, nullable=False, default=date.today)
    amount = Column(Numeric(18, 4), nullable=False)
    currency_code = Column(String(3), nullable=False, default="EGP")
    reference = Column(String(120), nullable=True)
    source_module = Column(String(80), nullable=True)
    source_entity = Column(String(80), nullable=True)
    source_id = Column(String(80), nullable=True)
    status = Column(String(20), nullable=False, default="posted", index=True)
    reversed_payment_id = Column(Integer, ForeignKey("treasury_payments.id", ondelete="RESTRICT"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_treasury_payment_amount"),
        CheckConstraint("party_type IN ('customer','supplier','other')", name="ck_treasury_payment_party"),
        CheckConstraint("direction IN ('receipt','payment')", name="ck_treasury_payment_direction"),
        CheckConstraint("status IN ('posted','reversed')", name="ck_treasury_payment_status"),
        Index("ix_treasury_payment_source", "company_id", "source_module", "source_entity", "source_id"),
    )
