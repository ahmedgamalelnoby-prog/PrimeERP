from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class JournalEntryLine(Base):
    __tablename__ = "journal_entry_lines"

    id = Column(Integer, primary_key=True, index=True)

    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    entry_id = Column(
        Integer,
        ForeignKey("journal_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number = Column(Integer, nullable=False)
    account_combination_id = Column(
        Integer,
        ForeignKey("account_combinations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    department_id = Column(
        Integer,
        ForeignKey("accounting_departments.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    cost_center_id = Column(
        Integer,
        ForeignKey("accounting_cost_centers.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    description = Column(Text, nullable=True)
    reference = Column(String(150), nullable=True)
    debit = Column(Numeric(20, 4), nullable=False, default=0)
    credit = Column(Numeric(20, 4), nullable=False, default=0)
    currency_code = Column(String(3), nullable=False, default="EGP")
    exchange_rate = Column(Numeric(18, 8), nullable=False, default=1)
    base_debit = Column(Numeric(20, 4), nullable=False, default=0)
    base_credit = Column(Numeric(20, 4), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    entry = relationship("JournalEntry", back_populates="lines")
    account_combination = relationship("AccountCombination")
    department = relationship("AccountingDepartment")
    cost_center = relationship("AccountingCostCenter")

    __table_args__ = (
        UniqueConstraint("entry_id", "line_number", name="uq_journal_entry_line_number"),
        CheckConstraint("line_number > 0", name="ck_journal_line_number_positive"),
        CheckConstraint("debit >= 0 AND credit >= 0", name="ck_journal_line_amounts_positive"),
        CheckConstraint("NOT (debit > 0 AND credit > 0)", name="ck_journal_line_single_side"),
        CheckConstraint("debit > 0 OR credit > 0", name="ck_journal_line_has_amount"),
        CheckConstraint("exchange_rate > 0", name="ck_journal_line_exchange_rate"),
        CheckConstraint("base_debit >= 0 AND base_credit >= 0", name="ck_journal_line_base_amounts_nonnegative"),
        Index("ix_journal_line_account_entry", "tenant_id", "account_combination_id", "entry_id"),
        Index("ix_journal_line_company_entry", "company_id", "entry_id"),
    )

    def __repr__(self) -> str:
        return f"<JournalEntryLine entry_id={self.entry_id} line={self.line_number}>"
