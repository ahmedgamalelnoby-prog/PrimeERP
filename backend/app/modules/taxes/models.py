"""Canonical tax-domain models.

TaxRate remains physically owned by Accounting. TaxReturnDraft owns the
periodic compliance workflow without duplicating the tax-rate master.
"""

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.sql import func

from app.database.base import Base
from app.modules.accounting.models import TaxRate


class TaxReturnDraft(Base):
    __tablename__ = "tax_return_drafts"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    jurisdiction_code = Column(String(30), nullable=False, default="EG")
    period_from = Column(Date, nullable=False)
    period_to = Column(Date, nullable=False)
    output_vat = Column(Numeric(18, 4), nullable=False, default=0)
    input_vat = Column(Numeric(18, 4), nullable=False, default=0)
    adjustments = Column(Numeric(18, 4), nullable=False, default=0)
    wht_payable = Column(Numeric(18, 4), nullable=False, default=0)
    net_vat = Column(Numeric(18, 4), nullable=False, default=0)
    reconciliation_difference = Column(Numeric(18, 4), nullable=False, default=0)
    is_reconciled = Column(Boolean, nullable=False, default=False)
    status = Column(String(30), nullable=False, default="draft", index=True)
    submission_reference = Column(String(255), nullable=True)
    submission_status = Column(String(30), nullable=False, default="not_supported")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


__all__ = ["TaxRate", "TaxReturnDraft"]
