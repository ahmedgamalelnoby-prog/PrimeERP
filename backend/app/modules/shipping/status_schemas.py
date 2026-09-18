from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class ShippingStatusCreate(BaseModel):
    company_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=50, pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=1, max_length=120)
    name_ar: str | None = Field(default=None, max_length=120)
    parent_code: str | None = Field(default=None, max_length=50)
    sort_order: int = Field(default=0, ge=0)
    is_active: bool = True
    financial_actions: list[str] = Field(default_factory=list)


class ShippingStatusResponse(ShippingStatusCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class FinancialEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    shipment_id: int
    event_key: str
    event_type: str
    event_date: date
    amount: Decimal
    debit_role: str
    credit_role: str
    source_status: str
    is_reversal: bool
    description: str | None
