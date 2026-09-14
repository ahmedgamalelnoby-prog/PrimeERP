from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryCreate(BaseModel):
    company_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=50)
    name_ar: str = Field(min_length=1, max_length=160)
    name_en: Optional[str] = Field(default=None, max_length=160)
    parent_id: Optional[int] = Field(default=None, gt=0)


class CategoryResponse(CategoryCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool


class PriceListCreate(BaseModel):
    company_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=160)
    currency: str = Field(default="EGP", min_length=3, max_length=3)
    channel: str = Field(default="default", max_length=30)
    is_default: bool = False

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()


class PriceListResponse(PriceListCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool


class PriceCreate(BaseModel):
    price_list_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    sale_price: Decimal = Field(ge=0)
    min_quantity: Decimal = Field(default=1, gt=0)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    source: str = Field(default="manual", max_length=30)

    @field_validator("valid_to")
    @classmethod
    def validate_valid_to(cls, value, info):
        valid_from = info.data.get("valid_from")
        if value is not None and valid_from is not None and value <= valid_from:
            raise ValueError("valid_to must be after valid_from")
        return value


class PriceResponse(PriceCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    is_active: bool
    created_at: datetime


class CostHistoryCreate(BaseModel):
    product_id: int = Field(gt=0)
    cost: Decimal = Field(ge=0)
    cost_type: str = Field(default="standard", max_length=30)
    source: str = Field(default="manual", max_length=50)
    effective_at: Optional[datetime] = None
    note: Optional[str] = None


class RecipeLineCreate(BaseModel):
    ingredient_product_id: int = Field(gt=0)
    quantity: Decimal = Field(gt=0)
    waste_percentage: Decimal = Field(default=0, ge=0, lt=100)
    uom_id: Optional[int] = Field(default=None, gt=0)
    notes: Optional[str] = Field(default=None, max_length=500)


class RecipeCreate(BaseModel):
    company_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=60)
    name_ar: str = Field(min_length=1, max_length=200)
    name_en: Optional[str] = Field(default=None, max_length=200)
    yield_quantity: Decimal = Field(default=1, gt=0)
    waste_percentage: Decimal = Field(default=0, ge=0, lt=100)
    lines: list[RecipeLineCreate] = Field(min_length=1)


class RecipeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    product_id: int
    code: str
    name_ar: str
    name_en: Optional[str]
    yield_quantity: Decimal
    waste_percentage: Decimal
    version: int
    is_active: bool
    lines: list[dict]
    total_cost: Decimal
    cost_per_yield: Decimal


class MenuCreate(BaseModel):
    company_id: int = Field(gt=0)
    branch_id: Optional[int] = Field(default=None, gt=0)
    code: str = Field(min_length=1, max_length=60)
    name_ar: str = Field(min_length=1, max_length=200)
    name_en: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = None


class MenuItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    price_list_id: Optional[int] = Field(default=None, gt=0)
    sale_price_override: Optional[Decimal] = Field(default=None, ge=0)
    display_order: int = Field(default=0, ge=0)
    is_available: bool = True
    is_featured: bool = False


class MenuItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    menu_id: int
    product_id: int
    price_list_id: Optional[int]
    sale_price_override: Optional[Decimal]
    display_order: int
    is_available: bool
    is_featured: bool


class MenuResponse(MenuCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool
    items: list[MenuItemResponse]


class PricingAnalysis(BaseModel):
    product_id: int
    product_name: str
    price_list_id: Optional[int]
    quantity: Decimal
    current_cost: Decimal
    sale_price: Decimal
    gross_margin: Decimal
    gross_margin_percentage: Decimal
    recommended_price_at_margin: Optional[Decimal]
    pricing_status: str
    price_source: str
    recipe_cost: Optional[Decimal]
    price_history: list[dict]
    cost_history: list[dict]


class PricingImpactItem(BaseModel):
    menu_id: Optional[int] = None
    menu_code: Optional[str] = None
    product_id: int
    product_name: str
    price_list_id: Optional[int]
    quantity: Decimal
    current_cost: Decimal
    sale_price: Decimal
    gross_margin_percentage: Decimal
    recommended_price_at_margin: Optional[Decimal]
    pricing_status: str
    price_source: str


class PricingImpactResponse(BaseModel):
    target_margin: Decimal
    below_margin: Decimal
    price_list_id: Optional[int]
    quantity: Decimal
    count: int
    items: list[PricingImpactItem]


class VariantCreate(BaseModel):
    product_id: int = Field(gt=0)
    sku: str = Field(min_length=1, max_length=100)
    name_ar: str = Field(min_length=1, max_length=200)
    name_en: Optional[str] = Field(default=None, max_length=200)
    attributes: dict = Field(default_factory=dict)
    uom_id: Optional[int] = Field(default=None, gt=0)
    sales_price: Decimal = Field(default=0, ge=0)
    purchase_price: Decimal = Field(default=0, ge=0)


class VariantBarcodeCreate(BaseModel):
    barcode: str = Field(min_length=1, max_length=120)
    barcode_type: str = Field(default="EAN", min_length=1, max_length=30)
    is_primary: bool = False
    variant_id: Optional[int] = Field(default=None, gt=0)


class BarcodeResponse(VariantBarcodeCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    product_id: int
    is_active: bool
    created_at: datetime


class VariantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    product_id: int
    sku: str
    name_ar: str
    name_en: Optional[str]
    attributes: dict
    uom_id: Optional[int]
    sales_price: Decimal
    purchase_price: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
    barcodes: list[BarcodeResponse] = []