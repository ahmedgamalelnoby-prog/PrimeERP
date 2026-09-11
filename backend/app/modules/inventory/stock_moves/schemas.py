from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_endpoints(self):
        if self.source_location_id is None and self.destination_location_id is None:
            raise ValueError("At least one stock move endpoint is required")
        if (
            self.source_location_id is not None
            and self.destination_location_id is not None
            and self.source_location_id == self.destination_location_id
        ):
            raise ValueError("Source and destination locations must be different")
        return self

    @field_validator("reference", "source_module", "source_entity", "source_id", "notes")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class StockMoveResponse(StockMoveCreate):
    id: int
    status: str

    model_config = ConfigDict(from_attributes=True)
