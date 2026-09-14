from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.sql import func
from app.database.base import Base


class Jurisdiction(Base):
    __tablename__ = "jurisdictions"
    id = Column(Integer, primary_key=True)
    code = Column(String(20), nullable=False, unique=True, index=True)
    country_code = Column(String(2), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    default_currency = Column(String(3), nullable=False)
    timezone = Column(String(80), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    __table_args__ = (CheckConstraint("length(country_code) = 2", name="ck_jurisdiction_country_code"), CheckConstraint("length(default_currency) = 3", name="ck_jurisdiction_currency"))


class CompanyJurisdiction(Base):
    __tablename__ = "company_jurisdictions"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    jurisdiction_id = Column(Integer, ForeignKey("jurisdictions.id", ondelete="RESTRICT"), nullable=False, index=True)
    role = Column(String(30), nullable=False, default="primary")
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    tax_resident = Column(Boolean, nullable=False, default=True)
    vat_registered = Column(Boolean, nullable=False, default=False)
    tax_ids = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    __table_args__ = (CheckConstraint("role IN ('primary','tax','permanent_establishment','registration')", name="ck_company_jurisdiction_role"), UniqueConstraint("company_id", "jurisdiction_id", "role", "effective_from", name="uq_company_jurisdiction_version"))


class PartnerJurisdiction(Base):
    __tablename__ = "partner_jurisdictions"
    id = Column(Integer, primary_key=True)
    partner_id = Column(Integer, ForeignKey("commerce_partners.id", ondelete="CASCADE"), nullable=False, index=True)
    jurisdiction_id = Column(Integer, ForeignKey("jurisdictions.id", ondelete="RESTRICT"), nullable=False, index=True)
    role = Column(String(30), nullable=False, default="residence")
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    tax_resident = Column(Boolean, nullable=False, default=True)
    vat_registered = Column(Boolean, nullable=False, default=False)
    tax_ids = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    __table_args__ = (CheckConstraint("role IN ('residence','tax','establishment','registration')", name="ck_partner_jurisdiction_role"), UniqueConstraint("partner_id", "jurisdiction_id", "role", "effective_from", name="uq_partner_jurisdiction_version"))


class TaxRule(Base):
    __tablename__ = "jurisdiction_tax_rules"
    id = Column(Integer, primary_key=True)
    jurisdiction_id = Column(Integer, ForeignKey("jurisdictions.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(80), nullable=False)
    name = Column(String(200), nullable=False)
    tax_type = Column(String(30), nullable=False)
    transaction_type = Column(String(40), nullable=False)
    taxpayer_type = Column(String(20), nullable=False, default="both")
    place_of_supply = Column(String(30), nullable=False, default="local")
    rate = Column(Numeric(12, 6), nullable=False, default=0)
    priority = Column(Integer, nullable=False, default=100)
    conditions = Column(JSON, nullable=False, default=dict)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    source_reference = Column(String(500), nullable=True)
    version = Column(String(40), nullable=False, default="1")
    is_active = Column(Boolean, nullable=False, default=True)
    __table_args__ = (CheckConstraint("tax_type IN ('vat','gst','sales_tax','wht','customs','other')", name="ck_tax_rule_type"), CheckConstraint("taxpayer_type IN ('b2b','b2c','both')", name="ck_tax_rule_taxpayer"), CheckConstraint("rate >= 0", name="ck_tax_rule_rate"), UniqueConstraint("jurisdiction_id", "code", "effective_from", name="uq_tax_rule_version"))


class JurisdictionDecision(Base):
    __tablename__ = "jurisdiction_decisions"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    partner_id = Column(Integer, ForeignKey("commerce_partners.id", ondelete="SET NULL"), nullable=True, index=True)
    jurisdiction_id = Column(Integer, ForeignKey("jurisdictions.id", ondelete="RESTRICT"), nullable=False, index=True)
    transaction_type = Column(String(40), nullable=False)
    transaction_date = Column(Date, nullable=False)
    place_of_supply = Column(String(30), nullable=False)
    b2b = Column(Boolean, nullable=False)
    rationale = Column(JSON, nullable=False, default=dict)
    rule_ids = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class TaxSnapshot(Base):
    """Immutable tax/legal facts captured at posting time."""
    __tablename__ = "tax_snapshots"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    document_kind = Column(String(20), nullable=False)
    document_id = Column(Integer, nullable=False)
    decision_id = Column(Integer, ForeignKey("jurisdiction_decisions.id", ondelete="RESTRICT"), nullable=False)
    jurisdiction_code = Column(String(20), nullable=False)
    country_code = Column(String(2), nullable=False)
    transaction_date = Column(Date, nullable=False)
    transaction_type = Column(String(40), nullable=False)
    place_of_supply = Column(String(30), nullable=False)
    b2b = Column(Boolean, nullable=False)
    facts = Column(JSON, nullable=False, default=dict)
    rules = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (
        UniqueConstraint("company_id", "document_kind", "document_id", name="uq_tax_snapshot_document"),
        CheckConstraint("document_kind IN ('sale','purchase','payment','credit_note','debit_note')", name="ck_tax_snapshot_document_kind"),
    )
