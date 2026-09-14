from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Index, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database.base import Base


class InventoryItem(Base):
    __tablename__ = "inventory_items"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("product_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    sku = Column(String(80), nullable=False)
    barcode = Column(String(80), nullable=True, index=True)
    name_ar = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=True)
    item_type = Column(String(30), nullable=False, default="stockable")
    uom = Column(String(30), nullable=False, default="unit")
    uom_id = Column(Integer, ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=True, index=True)
    sales_uom_id = Column(Integer, ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=True, index=True)
    purchase_uom_id = Column(Integer, ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=True, index=True)
    sales_tax_ids = Column(JSON, nullable=False, default=list)
    purchase_tax_ids = Column(JSON, nullable=False, default=list)
    costing_method = Column(String(20), nullable=False, default="weighted_average")
    standard_cost = Column(Numeric(18, 4), nullable=False, default=0)
    sales_price = Column(Numeric(18, 4), nullable=False, default=0)
    purchase_price = Column(Numeric(18, 4), nullable=False, default=0)
    reorder_level = Column(Numeric(18, 4), nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    description = Column(Text, nullable=True)
    __table_args__ = (
        UniqueConstraint("company_id", "sku", name="uq_inventory_item_company_sku"),
        UniqueConstraint("company_id", "barcode", name="uq_inventory_item_company_barcode"),
        CheckConstraint("item_type IN ('stockable','consumable','service','non_stock')", name="ck_inventory_item_type"),
        CheckConstraint("costing_method IN ('standard','weighted_average','fifo')", name="ck_inventory_item_costing_method"),
        CheckConstraint("standard_cost >= 0", name="ck_inventory_item_standard_cost"),
        CheckConstraint("sales_price >= 0", name="ck_inventory_item_sales_price"),
        CheckConstraint("purchase_price >= 0", name="ck_inventory_item_purchase_price"),
        CheckConstraint("reorder_level >= 0", name="ck_inventory_item_reorder_level"),
    )
    stocks = relationship("InventoryStock", back_populates="item", cascade="all, delete-orphan")
    uom_master = relationship("UnitOfMeasure", foreign_keys=[uom_id])
    sales_uom = relationship("UnitOfMeasure", foreign_keys=[sales_uom_id])
    purchase_uom = relationship("UnitOfMeasure", foreign_keys=[purchase_uom_id])
    category = relationship("ProductCategory", foreign_keys=[category_id])


class InventoryStock(Base):
    __tablename__ = "inventory_stocks"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("inventory_warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity_on_hand = Column(Numeric(18, 4), nullable=False, default=0)
    quantity_reserved = Column(Numeric(18, 4), nullable=False, default=0)
    average_cost = Column(Numeric(18, 4), nullable=False, default=0)
    item = relationship("InventoryItem", back_populates="stocks")
    variant = relationship("ProductVariant")
    warehouse = relationship("InventoryWarehouse", back_populates="stocks")
    __table_args__ = (
        Index("uq_inventory_stock_variant", "company_id", "item_id", "variant_id", "warehouse_id", unique=True, postgresql_where=variant_id.is_not(None)),
        Index("uq_inventory_stock_product", "company_id", "item_id", "warehouse_id", unique=True, postgresql_where=variant_id.is_(None)),
        CheckConstraint("quantity_on_hand >= 0", name="ck_inventory_stock_on_hand"),
        CheckConstraint("quantity_reserved >= 0", name="ck_inventory_stock_reserved"),
        CheckConstraint("average_cost >= 0", name="ck_inventory_stock_average_cost"),
    )
