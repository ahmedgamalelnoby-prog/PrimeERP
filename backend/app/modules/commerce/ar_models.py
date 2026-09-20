from datetime import datetime
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, CheckConstraint, func
from app.database.base import Base

class ARWriteOff(Base):
    __tablename__ = "ar_write_offs"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    partner_id = Column(Integer, ForeignKey("commerce_partners.id", ondelete="RESTRICT"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("sales_documents.id", ondelete="RESTRICT"), nullable=False, index=True)
    amount = Column(Numeric(18,4), nullable=False)
    reason = Column(Text, nullable=False)
    writeoff_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False)
    journal_id = Column(Integer, ForeignKey("accounting_journals.id", ondelete="RESTRICT"), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    requested_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    rejected_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    accounting_entry_id = Column(Integer, ForeignKey("journal_entries.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    __table_args__ = (CheckConstraint("amount > 0", name="ck_ar_writeoff_amount"), CheckConstraint("status IN ('pending','approved','rejected')", name="ck_ar_writeoff_status"))

class ARReconciliation(Base):
    __tablename__ = "ar_reconciliations"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    partner_id = Column(Integer, ForeignKey("commerce_partners.id", ondelete="RESTRICT"), nullable=True, index=True)
    as_of = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="balanced")
    discrepancy_amount = Column(Numeric(18,4), nullable=False, default=0)
    details_json = Column(Text, nullable=False, default="{}")
    reconciled_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
