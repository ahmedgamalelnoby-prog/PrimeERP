from decimal import Decimal
from pydantic import BaseModel, Field


class AdjustmentCreate(BaseModel):
    company_id: int = Field(gt=0)
    item_id: int = Field(gt=0)
    variant_id: int | None = Field(default=None, gt=0)
    location_id: int = Field(gt=0)
    quantity: Decimal = Field(gt=0)
    direction: str
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)
    reason: str = Field(min_length=1, max_length=100)
    reference: str | None = Field(default=None, max_length=100)
    notes: str | None = None

    def validate_direction(self):
        if self.direction not in {"increase", "decrease"}:
            raise ValueError("Direction must be increase or decrease")
        return self


class AdjustmentResponse(BaseModel):
    id: int
    company_id: int
    item_id: int
    variant_id: int | None
    location_id: int
    quantity: Decimal
    direction: str
    unit_cost: Decimal
    reason: str
    reference: str | None
    status: str
    notes: str | None

    model_config = {"from_attributes": True}
