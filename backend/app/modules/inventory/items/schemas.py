from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


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
    # uom is retained for compatibility; uom_id is the canonical master reference.
    uom: str = Field(default="unit", min_length=1, max_length=30)
    uom_id: Optional[int] = Field(default=None, gt=0)
    costing_method: CostingMethod = "weighted_average"
    standard_cost: Decimal = Field(default=0, ge=0)
    sales_price: Decimal = Field(default=0, ge=0)
    purchase_price: Decimal = Field(default=0, ge=0)
    reorder_level: Decimal = Field(default=0, ge=0)
    description: Optional[str] = None


class InventoryItemUpdate(BaseModel):
    barcode: Optional[str] = Field(default=None, max_length=80)
    name_ar: Optional[str] = Field(default=None, min_length=1, max_length=200)
    name_en: Optional[str] = Field(default=None, max_length=200)
    category_id: Optional[int] = Field(default=None, gt=0)
    item_type: Optional[ItemType] = None
    uom: Optional[str] = Field(default=None, min_length=1, max_length=30)
    uom_id: Optional[int] = Field(default=None, gt=0)
    costing_method: Optional[CostingMethod] = None
    standard_cost: Optional[Decimal] = Field(default=None, ge=0)
    sales_price: Optional[Decimal] = Field(default=None, ge=0)
    purchase_price: Optional[Decimal] = Field(default=None, ge=0)
    reorder_level: Optional[Decimal] = Field(default=None, ge=0)
    is_active: Optional[bool] = None
    description: Optional[str] = None


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
    costing_method: str
    standard_cost: Decimal
    sales_price: Decimal
    purchase_price: Decimal
    reorder_level: Decimal
    is_active: bool
    description: Optional[str]
