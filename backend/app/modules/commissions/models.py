from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.sql import func
from app.database.base import Base


class CommissionRule(Base):
    __tablename__ = "commission_rules"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(60), nullable=False)
    name = Column(String(200), nullable=False)
    basis = Column(String(30), nullable=False, default="net_sales")
    rate_percent = Column(Numeric(8, 4), nullable=False, default=0)
    fixed_amount = Column(Numeric(18, 4), nullable=False, default=0)
    min_base = Column(Numeric(18, 4), nullable=False, default=0)
    max_base = Column(Numeric(18, 4), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_commission_rule_company_code"),
        CheckConstraint("basis IN ('gross_sales','net_sales','gross_profit','collection')", name="ck_commission_rule_basis"),
        CheckConstraint("rate_percent >= 0 AND rate_percent <= 100", name="ck_commission_rule_rate"),
        CheckConstraint("fixed_amount >= 0 AND min_base >= 0", name="ck_commission_rule_nonnegative"),
        CheckConstraint("max_base IS NULL OR max_base >= min_base", name="ck_commission_rule_base_range"),
    )


class CommissionSettlement(Base):
    __tablename__ = "commission_settlements"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True)
    rule_id = Column(Integer, ForeignKey("commission_rules.id", ondelete="RESTRICT"), nullable=False, index=True)
    period = Column(String(7), nullable=False)
    source_type = Column(String(50), nullable=False)
    source_id = Column(Integer, nullable=True)
    base_amount = Column(Numeric(18, 4), nullable=False)
    commission_amount = Column(Numeric(18, 4), nullable=False)
    status = Column(String(20), nullable=False, default="draft")
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (
        CheckConstraint("base_amount >= 0 AND commission_amount >= 0", name="ck_commission_settlement_amounts"),
        CheckConstraint("status IN ('draft','approved','posted','cancelled')", name="ck_commission_settlement_status"),
        CheckConstraint("length(period) = 7 AND substr(period,5,1) = '-'", name="ck_commission_settlement_period"),
        UniqueConstraint("company_id", "employee_id", "rule_id", "period", "source_type", "source_id", name="uq_commission_settlement_source"),
    )
