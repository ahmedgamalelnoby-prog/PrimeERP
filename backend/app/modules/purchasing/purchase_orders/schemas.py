from datetime import date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field

PurchaseOrderStatus = Literal["draft", "approved", "partially_received", "received", "cancelled"]


class PurchaseOrderLineCreate(BaseModel):
    item_id: int = Field(gt=0)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)


class PurchaseOrderCreate(BaseModel):
    company_id: int = Field(gt=0)
    supplier_id: int = Field(gt=0)
    warehouse_id: int = Field(gt=0)
    order_number: str = Field(min_length=1, max_length=50)
    order_date: date
    reference: str | None = Field(default=None, max_length=100)
    notes: str | None = None
    lines: list[PurchaseOrderLineCreate] = Field(min_length=1)


class PurchaseOrderResponse(BaseModel):
    id: int
    company_id: int
    supplier_id: int
    warehouse_id: int
    order_number: str
    order_date: date
    status: PurchaseOrderStatus
    reference: str | None
    notes: str | None
    total_amount: Decimal
    model_config = {"from_attributes": True}
