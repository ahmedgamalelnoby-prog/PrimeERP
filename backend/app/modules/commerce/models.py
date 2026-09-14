from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import relationship
from app.database.base import Base


class BusinessPartner(Base):
    __tablename__ = "commerce_partners"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    partner_type = Column(String(20), nullable=False, default="customer")
    tax_number = Column(String(50), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)
    credit_limit = Column(Numeric(18, 4), nullable=False, default=0)
    payment_terms_days = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    __table_args__ = (CheckConstraint("partner_type IN ('customer','vendor','both')", name="ck_commerce_partner_type"),)


class SalesDocument(Base):
    __tablename__ = "sales_documents"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    partner_id = Column(Integer, ForeignKey("commerce_partners.id", ondelete="RESTRICT"), nullable=False, index=True)
    document_type = Column(String(20), nullable=False)
    number = Column(String(60), nullable=False, index=True)
    document_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="draft")
    warehouse_id = Column(Integer, ForeignKey("inventory_warehouses.id", ondelete="RESTRICT"), nullable=True)
    notes = Column(Text, nullable=True)
    subtotal = Column(Numeric(18, 4), nullable=False, default=0)
    tax_total = Column(Numeric(18, 4), nullable=False, default=0)
    discount_total = Column(Numeric(18, 4), nullable=False, default=0)
    total = Column(Numeric(18, 4), nullable=False, default=0)
    paid_total = Column(Numeric(18, 4), nullable=False, default=0)
    lines = relationship("SalesLine", back_populates="document", cascade="all, delete-orphan")
    __table_args__ = (
        CheckConstraint("document_type IN ('quotation','order','delivery','invoice','credit_note')", name="ck_sales_document_type"),
        CheckConstraint("status IN ('draft','confirmed','partially_fulfilled','fulfilled','cancelled','posted')", name="ck_sales_document_status"),
    )


class SalesLine(Base):
    __tablename__ = "sales_lines"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("sales_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=True, index=True)
    tax_rate_id = Column(Integer, ForeignKey("tax_rates.id", ondelete="RESTRICT"), nullable=True, index=True)
    tax_rate_ids = Column(JSON, nullable=False, default=list)
    description = Column(String(250), nullable=True)
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_price = Column(Numeric(18, 4), nullable=False)
    discount_percent = Column(Numeric(8, 4), nullable=False, default=0)
    tax_percent = Column(Numeric(8, 4), nullable=False, default=0)
    line_total = Column(Numeric(18, 4), nullable=False, default=0)
    document = relationship("SalesDocument", back_populates="lines")


class PurchaseDocument(Base):
    __tablename__ = "purchase_documents"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    partner_id = Column(Integer, ForeignKey("commerce_partners.id", ondelete="RESTRICT"), nullable=False, index=True)
    document_type = Column(String(20), nullable=False)
    number = Column(String(60), nullable=False)
    document_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="draft")
    warehouse_id = Column(Integer, ForeignKey("inventory_warehouses.id", ondelete="RESTRICT"), nullable=True)
    notes = Column(Text, nullable=True)
    subtotal = Column(Numeric(18, 4), nullable=False, default=0)
    tax_total = Column(Numeric(18, 4), nullable=False, default=0)
    discount_total = Column(Numeric(18, 4), nullable=False, default=0)
    total = Column(Numeric(18, 4), nullable=False, default=0)
    paid_total = Column(Numeric(18, 4), nullable=False, default=0)
    lines = relationship("PurchaseLine", back_populates="document", cascade="all, delete-orphan")
    __table_args__ = (
        CheckConstraint("document_type IN ('requisition','rfq','order','receipt','bill','debit_note')", name="ck_purchase_document_type"),
        CheckConstraint("status IN ('draft','confirmed','partially_received','received','cancelled','posted')", name="ck_purchase_document_status"),
    )


class PurchaseLine(Base):
    __tablename__ = "purchase_lines"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("purchase_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    tax_rate_id = Column(Integer, ForeignKey("tax_rates.id", ondelete="RESTRICT"), nullable=True, index=True)
    tax_rate_ids = Column(JSON, nullable=False, default=list)
    description = Column(String(250), nullable=True)
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_price = Column(Numeric(18, 4), nullable=False)
    discount_percent = Column(Numeric(8, 4), nullable=False, default=0)
    tax_percent = Column(Numeric(8, 4), nullable=False, default=0)
    line_total = Column(Numeric(18, 4), nullable=False, default=0)
    document = relationship("PurchaseDocument", back_populates="lines")


class CommercePayment(Base):
    __tablename__ = "commerce_payments"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    document_kind = Column(String(10), nullable=False)
    document_id = Column(Integer, nullable=False, index=True)
    payment_date = Column(Date, nullable=False)
    amount = Column(Numeric(18, 4), nullable=False)
    wht_amount = Column(Numeric(18, 4), nullable=False, default=0)
    method = Column(String(30), nullable=False)
    reference = Column(String(100), nullable=True)
    idempotency_key = Column(String(100), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="posted")
    reversed_of_id = Column(Integer, ForeignKey("commerce_payments.id", ondelete="RESTRICT"), nullable=True, index=True)
    reversed_at = Column(DateTime(timezone=True), nullable=True)
    __table_args__ = (
        CheckConstraint("document_kind IN ('sale','purchase')", name="ck_commerce_payment_kind"),
        CheckConstraint("amount > 0", name="ck_commerce_payment_amount"),
        CheckConstraint("wht_amount >= 0 AND wht_amount <= amount", name="ck_commerce_payment_wht"),
        CheckConstraint("status IN ('posted','reversed')", name="ck_commerce_payment_status"),
    )
