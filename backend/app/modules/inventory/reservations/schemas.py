from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


ReservationStatus = Literal["active", "released", "consumed", "cancelled"]


class ReservationCreate(BaseModel):
    company_id: int = Field(gt=0)
    item_id: int = Field(gt=0)
    location_id: int = Field(gt=0)
    quantity: Decimal = Field(gt=0)
    source_module: str = Field(min_length=1, max_length=80)
    source_entity: str = Field(min_length=1, max_length=80)
    source_id: str = Field(min_length=1, max_length=80)
    reference: str | None = Field(default=None, max_length=100)
    notes: str | None = None


class ReservationResponse(BaseModel):
    id: int
    company_id: int
    item_id: int
    location_id: int
    quantity: Decimal
    status: ReservationStatus
    source_module: str
    source_entity: str
    source_id: str
    reference: str | None
    notes: str | None

    model_config = {"from_attributes": True}
