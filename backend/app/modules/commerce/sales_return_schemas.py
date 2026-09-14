from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field


class SalesReturnLineCreate(BaseModel):
    original_delivery_line_id: int = Field(gt=0)
    quantity: Decimal = Field(gt=0)


class SalesReturnCreate(BaseModel):
    company_id: int = Field(gt=0)
    partner_id: int = Field(gt=0)
    number: str = Field(min_length=1, max_length=60)
    document_date: date
    warehouse_id: int | None = Field(default=None, gt=0)
    notes: str | None = None
    lines: list[SalesReturnLineCreate] = Field(min_length=1)
