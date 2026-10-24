import uuid

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    and_,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import foreign, relationship
from sqlalchemy.sql import func

from app.database.base import Base
from app.modules.accounting.fiscal_years.models.accounting_period import AccountingPeriod
from app.modules.accounting.fiscal_years.models.fiscal_year import FiscalYear
from app.modules.transactions.models import BusinessTransaction


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), nullable=False, unique=True, default=uuid.uuid4, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False, index=True)
    journal_id = Column(Integer, ForeignKey("accounting_journals.id", ondelete="RESTRICT"), nullable=False, index=True)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_years.id", ondelete="RESTRICT"), nullable=False, index=True)
    period_id = Column(Integer, ForeignKey("accounting_periods.id", ondelete="RESTRICT"), nullable=False, index=True)
    business_transaction_id = Column(Integer, ForeignKey("business_transactions.id", ondelete="RESTRICT"), nullable=True, index=True)
    reversal_of_id = Column(Integer, ForeignKey("journal_entries.id", ondelete="RESTRICT"), nullable=True, index=True)
    reversal_entry_id = Column(Integer, ForeignKey("journal_entries.id", ondelete="RESTRICT"), nullable=True, index=True)
    entry_number = Column(String(100), nullable=False, index=True)
    entry_date = Column(Date, nullable=False, index=True)
    posting_date = Column(Date, nullable=True, index=True)
    reference = Column(String(150), nullable=True, index=True)
    description = Column(Text, nullable=False)
    currency_code = Column(String(3), nullable=False, default="EGP")
    exchange_rate = Column(Numeric(18, 8), nullable=False, default=1)
    total_debit = Column(Numeric(20, 4), nullable=False, default=0)
    total_credit = Column(Numeric(20, 4), nullable=False, default=0)
    status = Column(String(30), nullable=False, default="draft", index=True)
    source_module = Column(String(80), nullable=True, index=True)
    source_entity = Column(String(100), nullable=True)
    source_id = Column(Integer, nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    submitted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    posted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    cancelled_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    journal = relationship("AccountingJournal", back_populates="entries")
    fiscal_year = relationship(
        "FiscalYear",
        primaryjoin=lambda: and_(
            foreign(JournalEntry.fiscal_year_id) == FiscalYear.id,
            JournalEntry.tenant_id == FiscalYear.tenant_id,
            JournalEntry.company_id == FiscalYear.company_id,
        ),
        foreign_keys=lambda: [JournalEntry.fiscal_year_id],
    )
    period = relationship(
        "AccountingPeriod",
        primaryjoin=lambda: and_(
            foreign(JournalEntry.period_id) == AccountingPeriod.id,
            JournalEntry.tenant_id == AccountingPeriod.tenant_id,
            JournalEntry.company_id == AccountingPeriod.company_id,
        ),
        foreign_keys=lambda: [JournalEntry.period_id],
    )
    business_transaction = relationship("BusinessTransaction")
    lines = relationship("JournalEntryLine", back_populates="entry", cascade="all, delete-orphan", passive_deletes=True, order_by="JournalEntryLine.line_number")
    reversal_of = relationship("JournalEntry", remote_side=[id], foreign_keys=[reversal_of_id], post_update=True)
    reversal_entry = relationship("JournalEntry", remote_side=[id], foreign_keys=[reversal_entry_id], post_update=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "entry_number", name="uq_journal_entry_tenant_number"),
        ForeignKeyConstraint(
            ["tenant_id", "company_id", "fiscal_year_id"],
            ["fiscal_years.tenant_id", "fiscal_years.company_id", "fiscal_years.id"],
            name="fk_journal_entry_fiscal_year_scope",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "company_id", "period_id"],
            ["accounting_periods.tenant_id", "accounting_periods.company_id", "accounting_periods.id"],
            name="fk_journal_entry_period_scope",
            ondelete="RESTRICT",
        ),
        CheckConstraint("total_debit >= 0", name="ck_journal_entry_debit_positive"),
        CheckConstraint("total_credit >= 0", name="ck_journal_entry_credit_positive"),
        CheckConstraint("exchange_rate > 0", name="ck_journal_entry_exchange_rate"),
        CheckConstraint("status IN ('draft', 'pending', 'approved', 'posted', 'cancelled', 'reversed')", name="ck_journal_entry_status"),
        Index("ix_journal_entry_scope_date", "tenant_id", "company_id", "branch_id", "entry_date"),
        Index("ix_journal_entry_source", "tenant_id", "source_module", "source_entity", "source_id"),
        Index("uq_journal_entry_source_idempotency", "tenant_id", "company_id", "source_module", "source_entity", "source_id", unique=True, postgresql_where="source_module IS NOT NULL AND source_entity IS NOT NULL AND source_id IS NOT NULL"),
    )

    def __repr__(self) -> str:
        return f"<JournalEntry number={self.entry_number!r} status={self.status!r}>"
