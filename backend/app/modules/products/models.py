from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String, TIMESTAMP, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base

class ProductCategory(Base):
    __tablename__="product_categories"
    id=Column(Integer,primary_key=True,index=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    name=Column(String(150),nullable=False)
    code=Column(String(50),nullable=False)
    is_active=Column(Boolean,nullable=False,default=True,server_default="true")
    __table_args__=(UniqueConstraint("tenant_id","code",name="uq_product_categories_tenant_code"),)

class ProductUnit(Base):
    __tablename__="product_units"
    id=Column(Integer,primary_key=True,index=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    name=Column(String(100),nullable=False)
    code=Column(String(30),nullable=False)
    precision=Column(Integer,nullable=False,default=3,server_default="3")
    is_active=Column(Boolean,nullable=False,default=True,server_default="true")
    __table_args__=(UniqueConstraint("tenant_id","code",name="uq_product_units_tenant_code"),)

class Product(Base):
    __tablename__="products"
    id=Column(Integer,primary_key=True,index=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    category_id=Column(Integer,ForeignKey("product_categories.id",ondelete="SET NULL"),nullable=True,index=True)
    unit_id=Column(Integer,ForeignKey("product_units.id",ondelete="RESTRICT"),nullable=False,index=True)
    sku=Column(String(80),nullable=False)
    name=Column(String(200),nullable=False,index=True)
    product_type=Column(String(30),nullable=False,default="stock",server_default="stock")
    barcode=Column(String(100),nullable=True,index=True)
    description=Column(Text,nullable=True)
    sale_price=Column(Numeric(18,2),nullable=False,default=0,server_default="0")
    cost_price=Column(Numeric(18,2),nullable=False,default=0,server_default="0")
    is_active=Column(Boolean,nullable=False,default=True,server_default="true",index=True)
    created_at=Column(TIMESTAMP(timezone=True),server_default=func.now(),nullable=False)
    updated_at=Column(TIMESTAMP(timezone=True),server_default=func.now(),onupdate=func.now(),nullable=False)
    category=relationship("ProductCategory",foreign_keys=[category_id])
    unit=relationship("ProductUnit",foreign_keys=[unit_id])
    __table_args__=(UniqueConstraint("tenant_id","sku",name="uq_products_tenant_sku"),)
