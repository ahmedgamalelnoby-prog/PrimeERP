from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.sql import func
from app.database.base import Base

class BankAccount(Base):
    __tablename__ = "treasury_bank_accounts"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    account_combination_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=True, index=True)
    name = Column(String(150), nullable=False)
    bank_name = Column(String(150), nullable=False)
    account_number = Column(String(100), nullable=True)
    currency = Column(String(10), nullable=False, default="EGP")
    opening_balance = Column(Numeric(18, 4), nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    __table_args__ = (UniqueConstraint("company_id", "name", name="uq_treasury_bank_account_company_name"))

class BankStatement(Base):
    __tablename__ = "treasury_bank_statements"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_account_id = Column(Integer, ForeignKey("treasury_bank_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    statement_number = Column(String(100), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    opening_balance = Column(Numeric(18, 4), nullable=False)
    closing_balance = Column(Numeric(18, 4), nullable=False)
    status = Column(String(20), nullable=False, default="open")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (UniqueConstraint("bank_account_id", "statement_number", name="uq_treasury_bank_statement_number"), CheckConstraint("period_end >= period_start", name="ck_treasury_bank_statement_dates"), CheckConstraint("status IN ('open','closed')", name="ck_treasury_bank_statement_status"))

class BankStatementLine(Base):
    __tablename__ = "treasury_bank_statement_lines"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    statement_id = Column(Integer, ForeignKey("treasury_bank_statements.id", ondelete="CASCADE"), nullable=False, index=True)
    external_id = Column(String(160), nullable=True)
    fingerprint = Column(String(64), nullable=False)
    transaction_date = Column(Date, nullable=False)
    value_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    reference = Column(String(150), nullable=True)
    cheque_number = Column(String(100), nullable=True)
    debit = Column(Numeric(18, 4), nullable=False, default=0)
    credit = Column(Numeric(18, 4), nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="EGP")
    matched_amount = Column(Numeric(18, 4), nullable=False, default=0)
    status = Column(String(20), nullable=False, default="unmatched")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (
        UniqueConstraint("statement_id", "fingerprint", name="uq_treasury_statement_line_fingerprint"),
        CheckConstraint("debit >= 0 AND credit >= 0", name="ck_treasury_statement_line_nonnegative"),
        CheckConstraint("NOT (debit > 0 AND credit > 0)", name="ck_treasury_statement_line_one_side"),
        CheckConstraint("matched_amount >= 0", name="ck_treasury_statement_line_matched"),
        CheckConstraint("status IN ('unmatched','partial','matched')", name="ck_treasury_statement_line_status"),
    )

class ReconciliationSession(Base):
    __tablename__ = "treasury_reconciliation_sessions"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_account_id = Column(Integer, ForeignKey("treasury_bank_accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    statement_id = Column(Integer, ForeignKey("treasury_bank_statements.id", ondelete="RESTRICT"), nullable=False, unique=True)
    book_balance = Column(Numeric(18, 4), nullable=False, default=0)
    bank_balance = Column(Numeric(18, 4), nullable=False, default=0)
    difference = Column(Numeric(18, 4), nullable=False, default=0)
    status = Column(String(20), nullable=False, default="open")
    closed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (CheckConstraint("status IN ('open','balanced','closed')", name="ck_treasury_reconciliation_status"),)

class ReconciliationMatch(Base):
    __tablename__ = "treasury_reconciliation_matches"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("treasury_reconciliation_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    statement_line_id = Column(Integer, ForeignKey("treasury_bank_statement_lines.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String(30), nullable=False)
    source_id = Column(Integer, nullable=False)
    amount = Column(Numeric(18, 4), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (
        UniqueConstraint("statement_line_id", "source_type", "source_id", name="uq_treasury_reconciliation_match_source"),
        CheckConstraint("amount > 0", name="ck_treasury_reconciliation_match_amount"),
    )
