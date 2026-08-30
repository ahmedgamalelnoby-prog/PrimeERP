from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class AccountingPeriod(Base):
    __tablename__ = "accounting_periods"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    tenant_id = Column(
        Integer,
        ForeignKey(
            "tenants.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey(
            "companies.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    fiscal_year_id = Column(
        Integer,
        ForeignKey(
            "fiscal_years.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    period_number = Column(
        Integer,
        nullable=False,
    )

    code = Column(
        String(30),
        nullable=False,
    )

    name_ar = Column(
        String(150),
        nullable=False,
    )

    name_en = Column(
        String(150),
        nullable=False,
    )

    start_date = Column(
        Date,
        nullable=False,
        index=True,
    )

    end_date = Column(
        Date,
        nullable=False,
        index=True,
    )

    status = Column(
        String(20),
        nullable=False,
        default="draft",
        index=True,
    )

    is_adjustment = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    allow_posting = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    opened_by = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    opened_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    closed_by = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    closed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_by = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    updated_by = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    fiscal_year = relationship(
        "FiscalYear",
        back_populates="periods",
    )

    __table_args__ = (
        UniqueConstraint(
            "fiscal_year_id",
            "period_number",
            name="uq_accounting_period_number",
        ),
        UniqueConstraint(
            "tenant_id",
            "company_id",
            "code",
            name="uq_accounting_period_scope_code",
        ),
        CheckConstraint(
            "end_date >= start_date",
            name="ck_accounting_period_valid_dates",
        ),
        CheckConstraint(
            "period_number > 0",
            name="ck_accounting_period_number_positive",
        ),
        CheckConstraint(
            "status IN "
            "('draft', 'open', 'closing', 'closed', 'locked')",
            name="ck_accounting_period_status",
        ),
        Index(
            "ix_accounting_period_scope_dates",
            "tenant_id",
            "company_id",
            "start_date",
            "end_date",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<AccountingPeriod "
            f"code={self.code!r} "
            f"status={self.status!r}>"
        )