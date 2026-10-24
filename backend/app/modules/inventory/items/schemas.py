from decimal import Decimal
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

ItemType = Literal["stockable", "consumable", "service", "non_stock"]
CostingMethod = Literal["standard", "weighted_average", "fifo"]

class InventoryItemCreate(BaseModel):
    company_id: int = Field(gt=0)
    sku: str = Field(min_length=1, max_length=80)
    barcode: Optional[str] = Field(default=None, max_length=80)
    name_ar: str = Field(min_length=1, max_length=200)
    name_en: Optional[str] = Field(default=None, max_length=200)
    category_id: Optional[int] = Field(default=None, gt=0)
    item_type: ItemType = "stockable"
    uom: str = Field(default="unit", min_length=1, max_length=30)
    uom_id: Optional[int] = Field(default=None, gt=0)
    sales_uom_id: Optional[int] = Field(default=None, gt=0)
    purchase_uom_id: Optional[int] = Field(default=None, gt=0)
    sales_tax_ids: list[int] = Field(default_factory=list)
    purchase_tax_ids: list[int] = Field(default_factory=list)
    costing_method: CostingMethod = "weighted_average"
    standard_cost: Decimal = Field(default=0, ge=0)
    sales_price: Decimal = Field(default=0, ge=0)
    purchase_price: Decimal = Field(default=0, ge=0)
    reorder_level: Decimal = Field(default=0, ge=0)
    batch_tracking: bool | None = None
    serial_tracking: bool | None = None
    expiry_tracking: bool | None = None
    description: Optional[str] = None
    @field_validator("sales_tax_ids", "purchase_tax_ids")
    @classmethod
    def validate_tax_ids(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("Duplicate tax ids are not allowed")
        if any(tax_id <= 0 for tax_id in value):
            raise ValueError("Tax ids must be positive")
        return value

class InventoryItemUpdate(BaseModel):
    barcode: Optional[str] = Field(default=None, max_length=80)
    name_ar: Optional[str] = Field(default=None, min_length=1, max_length=200)
    name_en: Optional[str] = Field(default=None, max_length=200)
    category_id: Optional[int] = Field(default=None, gt=0)
    item_type: Optional[ItemType] = None
    uom: Optional[str] = Field(default=None, min_length=1, max_length=30)
    uom_id: Optional[int] = Field(default=None, gt=0)
    sales_uom_id: Optional[int] = Field(default=None, gt=0)
    purchase_uom_id: Optional[int] = Field(default=None, gt=0)
    sales_tax_ids: Optional[list[int]] = None
    purchase_tax_ids: Optional[list[int]] = None
    costing_method: Optional[CostingMethod] = None
    standard_cost: Optional[Decimal] = Field(default=None, ge=0)
    sales_price: Optional[Decimal] = Field(default=None, ge=0)
    purchase_price: Optional[Decimal] = Field(default=None, ge=0)
    reorder_level: Optional[Decimal] = Field(default=None, ge=0)
    batch_tracking: Optional[bool] = None
    serial_tracking: Optional[bool] = None
    expiry_tracking: Optional[bool] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None
    @field_validator("batch_tracking", "serial_tracking", "expiry_tracking", mode="before")
    @classmethod
    def tracking_flags_cannot_be_null(cls, value):
        if value is None:
            raise ValueError("Tracking flags cannot be null; use true or false")
        return value

    @field_validator("sales_tax_ids", "purchase_tax_ids")
    @classmethod
    def validate_tax_ids(cls, value):
        if value is not None and len(value) != len(set(value)):
            raise ValueError("Duplicate tax ids are not allowed")
        if value is not None and any(tax_id <= 0 for tax_id in value):
            raise ValueError("Tax ids must be positive")
        return value

class InventoryItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    category_id: Optional[int]
    sku: str
    barcode: Optional[str]
    name_ar: str
    name_en: Optional[str]
    item_type: str
    uom: str
    uom_id: Optional[int]
    sales_uom_id: Optional[int]
    purchase_uom_id: Optional[int]
    sales_tax_ids: list[int]
    purchase_tax_ids: list[int]
    costing_method: str
    standard_cost: Decimal
    sales_price: Decimal
    purchase_price: Decimal
    reorder_level: Decimal
    batch_tracking: bool
    serial_tracking: bool
    expiry_tracking: bool
    is_active: bool
    description: Optional[str]
