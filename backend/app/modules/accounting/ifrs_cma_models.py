from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.database.base import Base
from app.modules.accounting.chart_of_accounts.models import AccountingCostCenter

# Backward-compatible public name for the IFRS/CMA foundation.
CostCenter = AccountingCostCenter


class AccountingPolicy(Base):
    __tablename__ = "accounting_policies"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    jurisdiction = Column(String(20), nullable=False, default="EG")
    accounting_framework = Column(String(30), nullable=False, default="IFRS")
    management_framework = Column(String(30), nullable=False, default="CMA")
    functional_currency = Column(String(3), nullable=False, default="EGP")
    presentation_currency = Column(String(3), nullable=False, default="EGP")
    tax_authority = Column(String(50), nullable=False, default="EGYPT_ETA")
    tax_inclusive = Column(Boolean, nullable=False, default=False)
    require_period_close = Column(Boolean, nullable=False, default=True)
    require_posting_approval = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __init__(self, **kwargs):
        kwargs.setdefault("jurisdiction", "EG")
        kwargs.setdefault("accounting_framework", "IFRS")
        kwargs.setdefault("management_framework", "CMA")
        kwargs.setdefault("functional_currency", "EGP")
        kwargs.setdefault("presentation_currency", "EGP")
        kwargs.setdefault("tax_authority", "EGYPT_ETA")
        kwargs.setdefault("tax_inclusive", False)
        kwargs.setdefault("require_period_close", True)
        kwargs.setdefault("require_posting_approval", True)
        super().__init__(**kwargs)

    __table_args__ = (
        UniqueConstraint("company_id", name="uq_accounting_policy_company"),
        CheckConstraint("accounting_framework IN ('IFRS','IFRS_SME','LOCAL')", name="ck_accounting_policy_framework"),
        CheckConstraint("management_framework IN ('CMA','MANAGEMENT_ACCOUNTING')", name="ck_accounting_policy_management"),
        CheckConstraint("length(functional_currency) = 3", name="ck_accounting_policy_functional_currency"),
    )


class FiscalPeriod(Base):
    __tablename__ = "accounting_fiscal_periods"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(80), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="open")
    closed_at = Column(DateTime(timezone=True), nullable=True)
    closed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    __table_args__ = (
        UniqueConstraint("company_id", "start_date", "end_date", name="uq_fiscal_period_company_dates"),
        CheckConstraint("end_date >= start_date", name="ck_fiscal_period_dates"),
        CheckConstraint("status IN ('open','soft_closed','closed')", name="ck_fiscal_period_status"),
    )


class ChartOfAccount(Base):
    __tablename__ = "accounting_accounts"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(30), nullable=False)
    name_ar = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=True)
    account_type = Column(String(30), nullable=False)
    parent_id = Column(Integer, ForeignKey("accounting_accounts.id", ondelete="RESTRICT"), nullable=True)
    normal_balance = Column(String(10), nullable=False)
    is_control_account = Column(Boolean, nullable=False, default=False)
    allow_manual_posting = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_accounting_account_company_code"),
        CheckConstraint("account_type IN ('asset','liability','equity','revenue','expense','contra_asset','contra_revenue','contra_liability')", name="ck_accounting_account_type"),
        CheckConstraint("normal_balance IN ('debit','credit')", name="ck_accounting_account_normal_balance"),
    )


class IFRSJournalEntry(Base):
    __tablename__ = "accounting_journal_entries"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    fiscal_period_id = Column(Integer, ForeignKey("accounting_fiscal_periods.id", ondelete="RESTRICT"), nullable=False, index=True)
    entry_no = Column(String(40), nullable=False)
    entry_date = Column(Date, nullable=False)
    description = Column(Text, nullable=False)
    source_module = Column(String(80), nullable=False)
    source_entity = Column(String(80), nullable=False)
    source_id = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="draft")
    approved_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (
        UniqueConstraint("company_id", "entry_no", name="uq_journal_entry_company_no"),
        UniqueConstraint("company_id", "source_module", "source_entity", "source_id", name="uq_journal_entry_source"),
        CheckConstraint("status IN ('draft','approved','posted','reversed')", name="ck_journal_entry_status"),
    )


class JournalLine(Base):
    __tablename__ = "accounting_journal_lines"
    id = Column(Integer, primary_key=True)
    journal_entry_id = Column(Integer, ForeignKey("accounting_journal_entries.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounting_accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    cost_center_id = Column(Integer, ForeignKey("accounting_cost_centers.id", ondelete="RESTRICT"), nullable=True, index=True)
    description = Column(Text, nullable=True)
    debit = Column(Numeric(20, 4), nullable=False, default=0)
    credit = Column(Numeric(20, 4), nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="EGP")
    exchange_rate = Column(Numeric(20, 8), nullable=False, default=1)
    __table_args__ = (
        CheckConstraint("debit >= 0 AND credit >= 0", name="ck_journal_line_nonnegative"),
        CheckConstraint("NOT (debit > 0 AND credit > 0)", name="ck_journal_line_one_side"),
        CheckConstraint("debit > 0 OR credit > 0", name="ck_journal_line_nonzero"),
    )


class ManagementBudget(Base):
    __tablename__ = "accounting_management_budgets"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(160), nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="draft")
    version = Column(Integer, nullable=False, default=1)
    __table_args__ = (
        UniqueConstraint("company_id", "name", "version", name="uq_management_budget_version"),
        CheckConstraint("status IN ('draft','approved','locked')", name="ck_management_budget_status"),
    )


class ManagementBudgetLine(Base):
    __tablename__ = "accounting_management_budget_lines"
    id = Column(Integer, primary_key=True)
    budget_id = Column(Integer, ForeignKey("accounting_management_budgets.id", ondelete="CASCADE"), nullable=False, index=True)
    cost_center_id = Column(Integer, ForeignKey("accounting_cost_centers.id", ondelete="RESTRICT"), nullable=True, index=True)
    account_id = Column(Integer, ForeignKey("accounting_accounts.id", ondelete="RESTRICT"), nullable=True, index=True)
    period_month = Column(Integer, nullable=False)
    amount = Column(Numeric(20, 4), nullable=False)
    __table_args__ = (
        CheckConstraint("period_month BETWEEN 1 AND 12", name="ck_budget_line_month"),
        CheckConstraint("amount >= 0", name="ck_budget_line_amount"),
    )


# Public compatibility alias without registering a second ORM class named JournalEntry.
JournalEntry = IFRSJournalEntry
