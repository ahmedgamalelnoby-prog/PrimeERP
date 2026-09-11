from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, String, Text, Index
from app.database.base import Base

class BankAccount(Base):
    __tablename__ = "bank_accounts"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(40), nullable=False)
    name = Column(String(120), nullable=False)
    currency_code = Column(String(3), nullable=False, default="EGP")
    opening_balance = Column(Numeric(18,4), nullable=False, default=0)
    is_active = Column(Integer, nullable=False, default=1)
    __table_args__ = (Index("uq_bank_account_company_code", "company_id", "code", unique=True),)

class BankStatementLine(Base):
    __tablename__ = "bank_statement_lines"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_account_id = Column(Integer, ForeignKey("bank_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    statement_date = Column(Date, nullable=False)
    value_date = Column(Date, nullable=True)
    reference = Column(String(120), nullable=True)
    description = Column(Text, nullable=True)
    amount = Column(Numeric(18,4), nullable=False)
    direction = Column(String(10), nullable=False)
    status = Column(String(20), nullable=False, default="unmatched", index=True)
    matched_payment_id = Column(Integer, ForeignKey("treasury_payments.id", ondelete="SET NULL"), nullable=True)
    __table_args__ = (Index("ix_bank_statement_account_date", "bank_account_id", "statement_date"),)
