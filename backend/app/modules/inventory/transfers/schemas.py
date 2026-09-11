from decimal import Decimal
from pydantic import BaseModel, Field


class TransferLineCreate(BaseModel):
    item_id: int = Field(gt=0)
    source_location_id: int = Field(gt=0)
    destination_location_id: int = Field(gt=0)
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)


class TransferCreate(BaseModel):
    company_id: int = Field(gt=0)
    source_warehouse_id: int = Field(gt=0)
    destination_warehouse_id: int = Field(gt=0)
    reference: str = Field(min_length=1, max_length=100)
    notes: str | None = None
    lines: list[TransferLineCreate] = Field(min_length=1)


class TransferResponse(BaseModel):
    id: int
    company_id: int
    source_warehouse_id: int
    destination_warehouse_id: int
    reference: str
    status: str
    notes: str | None

    model_config = {"from_attributes": True}
