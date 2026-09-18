from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.base import Base


class ProductBundle(Base):
    __tablename__ = "product_bundles"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    catalog_product_id = Column(Integer, ForeignKey("catalog_products.id", ondelete="RESTRICT"), nullable=True, index=True)
    code = Column(String(60), nullable=False)
    name_ar = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_product_bundle_company_code"), UniqueConstraint("company_id", "product_id", name="uq_product_bundle_company_product"))
    lines = relationship("ProductBundleLine", back_populates="bundle", cascade="all, delete-orphan", order_by="ProductBundleLine.line_no")


class ProductBundleLine(Base):
    __tablename__ = "product_bundle_lines"
    id = Column(Integer, primary_key=True, index=True)
    bundle_id = Column(Integer, ForeignKey("product_bundles.id", ondelete="CASCADE"), nullable=False, index=True)
    line_no = Column(Integer, nullable=False)
    component_product_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    component_item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=True, index=True)
    quantity = Column(Numeric(18, 6), nullable=False)
    __table_args__ = (UniqueConstraint("bundle_id", "line_no", name="uq_product_bundle_line_no"), UniqueConstraint("bundle_id", "component_product_id", name="uq_product_bundle_component"), CheckConstraint("line_no > 0", name="ck_product_bundle_line_no_positive"), CheckConstraint("quantity > 0", name="ck_product_bundle_line_quantity_positive"))
    bundle = relationship("ProductBundle", back_populates="lines")
