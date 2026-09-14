from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class ProductCategory(Base):
    __tablename__ = "product_categories"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("product_categories.id", ondelete="RESTRICT"), nullable=True, index=True)
    code = Column(String(50), nullable=False)
    name_ar = Column(String(160), nullable=False)
    name_en = Column(String(160), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_product_category_company_code"),)
    parent = relationship("ProductCategory", remote_side=[id], backref="children")


class ProductPriceList(Base):
    __tablename__ = "product_price_lists"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(160), nullable=False)
    currency = Column(String(3), nullable=False, default="EGP")
    channel = Column(String(30), nullable=False, default="default")
    is_default = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_price_list_company_code"),)


class ProductPrice(Base):
    __tablename__ = "product_prices"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    price_list_id = Column(Integer, ForeignKey("product_price_lists.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True)
    sale_price = Column(Numeric(18, 4), nullable=False)
    min_quantity = Column(Numeric(18, 4), nullable=False, default=1)
    valid_from = Column(DateTime, nullable=False, server_default=func.now())
    valid_to = Column(DateTime, nullable=True)
    source = Column(String(30), nullable=False, default="manual")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    __table_args__ = (CheckConstraint("sale_price >= 0", name="ck_product_price_nonnegative"), CheckConstraint("min_quantity > 0", name="ck_product_price_min_qty"))
    price_list = relationship("ProductPriceList")
    product = relationship("InventoryItem")


class ProductCostHistory(Base):
    __tablename__ = "product_cost_history"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True)
    cost = Column(Numeric(18, 4), nullable=False)
    cost_type = Column(String(30), nullable=False, default="standard")
    source = Column(String(50), nullable=False, default="manual")
    effective_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    note = Column(Text, nullable=True)
    __table_args__ = (CheckConstraint("cost >= 0", name="ck_product_cost_nonnegative"),)


class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    code = Column(String(60), nullable=False)
    name_ar = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=True)
    yield_quantity = Column(Numeric(18, 4), nullable=False, default=1)
    waste_percentage = Column(Numeric(7, 4), nullable=False, default=0)
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    __table_args__ = (UniqueConstraint("company_id", "code", "version", name="uq_recipe_company_code_version"), UniqueConstraint("company_id", "product_id", "version", name="uq_recipe_company_product_version"), CheckConstraint("yield_quantity > 0", name="ck_recipe_yield_positive"), CheckConstraint("waste_percentage >= 0 AND waste_percentage < 100", name="ck_recipe_waste_range"))
    product = relationship("InventoryItem")
    lines = relationship("RecipeLine", back_populates="recipe", cascade="all, delete-orphan", order_by="RecipeLine.line_no")


class RecipeLine(Base):
    __tablename__ = "recipe_lines"
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False, index=True)
    line_no = Column(Integer, nullable=False)
    ingredient_product_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Numeric(18, 6), nullable=False)
    waste_percentage = Column(Numeric(7, 4), nullable=False, default=0)
    uom_id = Column(Integer, ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=True)
    conversion_factor_to_product_uom = Column(Numeric(18, 8), nullable=False, default=1)
    notes = Column(String(500), nullable=True)
    __table_args__ = (UniqueConstraint("recipe_id", "line_no", name="uq_recipe_line_no"), CheckConstraint("line_no > 0", name="ck_recipe_line_no_positive"), CheckConstraint("quantity > 0", name="ck_recipe_line_quantity_positive"), CheckConstraint("waste_percentage >= 0 AND waste_percentage < 100", name="ck_recipe_line_waste_range"), CheckConstraint("conversion_factor_to_product_uom > 0", name="ck_recipe_line_conversion_positive"))
    recipe = relationship("Recipe", back_populates="lines")
    ingredient = relationship("InventoryItem")


class Menu(Base):
    __tablename__ = "menus"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=True, index=True)
    code = Column(String(60), nullable=False)
    name_ar = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_menu_company_code"),)
    items = relationship("MenuItem", back_populates="menu", cascade="all, delete-orphan", order_by="MenuItem.display_order")


class MenuItem(Base):
    __tablename__ = "menu_items"
    id = Column(Integer, primary_key=True, index=True)
    menu_id = Column(Integer, ForeignKey("menus.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    price_list_id = Column(Integer, ForeignKey("product_price_lists.id", ondelete="RESTRICT"), nullable=True, index=True)
    sale_price_override = Column(Numeric(18, 4), nullable=True)
    display_order = Column(Integer, nullable=False, default=0)
    is_available = Column(Boolean, nullable=False, default=True)
    is_featured = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    __table_args__ = (UniqueConstraint("menu_id", "product_id", name="uq_menu_product"), CheckConstraint("sale_price_override IS NULL OR sale_price_override >= 0", name="ck_menu_override_price"))
    menu = relationship("Menu", back_populates="items")
    product = relationship("InventoryItem")
    price_list = relationship("ProductPriceList")


class ProductVariant(Base):
    __tablename__ = "product_variants"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True)
    sku = Column(String(100), nullable=False)
    name_ar = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=True)
    attributes = Column(Text, nullable=False, default="{}")
    uom_id = Column(Integer, ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=True)
    sales_price = Column(Numeric(18, 4), nullable=False, default=0)
    purchase_price = Column(Numeric(18, 4), nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    __table_args__ = (UniqueConstraint("company_id", "sku", name="uq_product_variant_company_sku"), CheckConstraint("sales_price >= 0", name="ck_product_variant_sales_price"), CheckConstraint("purchase_price >= 0", name="ck_product_variant_purchase_price"))
    product = relationship("InventoryItem")
    uom = relationship("UnitOfMeasure")
    barcodes = relationship("ProductBarcode", back_populates="variant", cascade="all, delete-orphan")


class ProductBarcode(Base):
    __tablename__ = "product_barcodes"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=True, index=True)
    barcode = Column(String(120), nullable=False)
    barcode_type = Column(String(30), nullable=False, default="EAN")
    is_primary = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    __table_args__ = (UniqueConstraint("company_id", "barcode", name="uq_product_barcode_company_code"),)
    product = relationship("InventoryItem")
    variant = relationship("ProductVariant", back_populates="barcodes")
