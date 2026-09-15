from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class FiscalYear(Base):
    __tablename__ = "fiscal_years"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(30), nullable=False)
    name_ar = Column(String(150), nullable=False)
    name_en = Column(String(150), nullable=False)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    status = Column(String(20), nullable=False, default="draft", index=True)
    is_current = Column(Boolean, nullable=False, default=False, index=True)
    is_adjustment_period_enabled = Column(Boolean, nullable=False, default=False)
    opened_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    closed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    periods = relationship(
        "AccountingPeriod",
        back_populates="fiscal_year",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="AccountingPeriod.period_number",
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "company_id", "code", name="uq_fiscal_year_tenant_company_code"),
        UniqueConstraint("tenant_id", "company_id", "id", name="uq_fiscal_year_tenant_company_id"),
        ForeignKeyConstraint(
            ["tenant_id", "company_id"],
            ["companies.tenant_id", "companies.id"],
            name="fk_fiscal_year_company_tenant",
            ondelete="CASCADE",
        ),
        CheckConstraint("end_date >= start_date", name="ck_fiscal_year_valid_dates"),
        CheckConstraint("status IN ('draft', 'open', 'closing', 'closed')", name="ck_fiscal_year_status"),
        Index("ix_fiscal_year_scope_dates", "tenant_id", "company_id", "start_date", "end_date"),
    )

    def __repr__(self) -> str:
        return f"<FiscalYear code={self.code!r} status={self.status!r}>"
