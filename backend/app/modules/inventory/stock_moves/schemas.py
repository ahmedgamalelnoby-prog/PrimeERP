from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

MovementType = Literal["receipt", "issue", "transfer", "adjustment", "opening", "return"]


class StockMoveCreate(BaseModel):
    company_id: int = Field(gt=0)
    item_id: int = Field(gt=0)
    source_location_id: int | None = Field(default=None, gt=0)
    destination_location_id: int | None = Field(default=None, gt=0)
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)
    movement_type: MovementType
    reference: str | None = Field(default=None, max_length=100)
    source_module: str | None = Field(default=None, max_length=80)
    source_entity: str | None = Field(default=None, max_length=80)
    source_id: str | None = Field(default=None, max_length=80)
    notes: str | None = None


class StockMoveResponse(StockMoveCreate):
    id: int
    status: str

    class Config:
        from_attributes = True
