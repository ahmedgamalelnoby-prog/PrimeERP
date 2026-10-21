from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
class CategoryBase(BaseModel):
    name:str=Field(min_length=1,max_length=150); code:str=Field(min_length=1,max_length=50); is_active:bool=True
class CategoryCreate(CategoryBase): pass
class CategoryUpdate(BaseModel):
    name:str|None=Field(default=None,min_length=1,max_length=150); code:str|None=Field(default=None,min_length=1,max_length=50); is_active:bool|None=None
class CategoryRead(CategoryBase):
    model_config=ConfigDict(from_attributes=True); id:int; tenant_id:int
class UnitBase(BaseModel):
    name:str=Field(min_length=1,max_length=100); code:str=Field(min_length=1,max_length=30); precision:int=Field(default=3,ge=0,le=10); is_active:bool=True
class UnitCreate(UnitBase): pass
class UnitUpdate(BaseModel):
    name:str|None=Field(default=None,min_length=1,max_length=100); code:str|None=Field(default=None,min_length=1,max_length=30); precision:int|None=Field(default=None,ge=0,le=10); is_active:bool|None=None
class UnitRead(UnitBase):
    model_config=ConfigDict(from_attributes=True); id:int; tenant_id:int
class ProductBase(BaseModel):
    category_id:int|None=None; unit_id:int; sku:str=Field(min_length=1,max_length=80); name:str=Field(min_length=1,max_length=200); product_type:str=Field(default="stock",max_length=30); barcode:str|None=Field(default=None,max_length=100); description:str|None=None; sale_price:Decimal=Field(default=0,ge=0); cost_price:Decimal=Field(default=0,ge=0); is_active:bool=True
class ProductCreate(ProductBase): pass
class ProductUpdate(BaseModel):
    category_id:int|None=None; unit_id:int|None=None; sku:str|None=Field(default=None,min_length=1,max_length=80); name:str|None=Field(default=None,min_length=1,max_length=200); product_type:str|None=Field(default=None,max_length=30); barcode:str|None=Field(default=None,max_length=100); description:str|None=None; sale_price:Decimal|None=Field(default=None,ge=0); cost_price:Decimal|None=Field(default=None,ge=0); is_active:bool|None=None
class ProductRead(ProductBase):
    model_config=ConfigDict(from_attributes=True); id:int; tenant_id:int
