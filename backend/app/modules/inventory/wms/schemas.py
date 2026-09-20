from datetime import date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field

OperationType = Literal["receiving","putaway","picking","packing","dispatch","cycle_count"]

class WMSLineCreate(BaseModel):
    item_id: int = Field(gt=0)
    variant_id: int | None = Field(default=None, gt=0)
    source_location_id: int | None = Field(default=None, gt=0)
    destination_location_id: int | None = Field(default=None, gt=0)
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)
    lot_number: str | None = Field(default=None, max_length=100)
    serial_number: str | None = Field(default=None, max_length=100)
    expiry_date: date | None = None
    barcode: str | None = Field(default=None, max_length=100)
    count_expected: Decimal | None = Field(default=None, ge=0)
    count_actual: Decimal | None = Field(default=None, ge=0)

class WMSOperationCreate(BaseModel):
    company_id: int = Field(gt=0)
    warehouse_id: int = Field(gt=0)
    operation_type: OperationType
    reference: str = Field(min_length=1, max_length=100)
    notes: str | None = None
    lines: list[WMSLineCreate] = Field(min_length=1)

class WMSOperationResponse(BaseModel):
    id: int
    company_id: int
    warehouse_id: int
    operation_type: str
    reference: str
    status: str
    lines: list
    class Config:
        from_attributes = True
