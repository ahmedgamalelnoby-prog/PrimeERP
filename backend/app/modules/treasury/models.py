from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from app.database.base import Base


class Cheque(Base):
    __tablename__ = "treasury_cheques"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    partner_id = Column(Integer, ForeignKey("commerce_partners.id", ondelete="RESTRICT"), nullable=True, index=True)
    direction = Column(String(10), nullable=False)  # received / issued
    cheque_number = Column(String(100), nullable=False)
    bank_name = Column(String(150), nullable=True)
    account_number = Column(String(100), nullable=True)
    cheque_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    amount = Column(Numeric(18, 4), nullable=False)
    currency = Column(String(10), nullable=False, default="EGP")
    status = Column(String(30), nullable=False, default="received")
    source_payment_id = Column(Integer, ForeignKey("commerce_payments.id", ondelete="SET NULL"), nullable=True, index=True)
    original_cheque_id = Column(Integer, ForeignKey("treasury_cheques.id", ondelete="SET NULL"), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint("direction IN ('received','issued')", name="ck_treasury_cheque_direction"),
        CheckConstraint("amount > 0", name="ck_treasury_cheque_amount"),
        CheckConstraint("status IN ('received','deposited','under_collection','collected','returned','resubmitted','issued','cleared','cancelled','reversed')", name="ck_treasury_cheque_status"),
        CheckConstraint("due_date >= cheque_date", name="ck_treasury_cheque_dates"),
    )


class ChequeEvent(Base):
    __tablename__ = "treasury_cheque_events"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    cheque_id = Column(Integer, ForeignKey("treasury_cheques.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(40), nullable=False)
    from_status = Column(String(30), nullable=True)
    to_status = Column(String(30), nullable=False)
    event_date = Column(Date, nullable=False)
    reference = Column(String(150), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
