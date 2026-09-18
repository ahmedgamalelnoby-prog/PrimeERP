from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

RuleType = Literal[
    "base", "zone", "weight", "pieces", "order_value", "cod", "cod_collected",
    "card", "tier", "minimum", "remote", "rto", "exchange", "storage"
]


class PricingProfileCreate(BaseModel):
    company_id: int = Field(gt=0)
    carrier_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=150)
    effective_from: date
    effective_to: date | None = None
    priority: int = Field(default=100, ge=0)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.effective_to and self.effective_to < self.effective_from:
            raise ValueError("effective_to cannot be before effective_from")
        return self


class PricingProfileResponse(PricingProfileCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool


class PricingRuleCreate(BaseModel):
    profile_id: int = Field(gt=0)
    rule_type: RuleType
    basis: Literal["order", "weight", "pieces", "order_value", "cod", "cod_collected", "storage_days"] = "order"
    zone_code: str | None = None
    min_value: Decimal | None = Field(default=None, ge=0)
    max_value: Decimal | None = Field(default=None, ge=0)
    included_units: Decimal = Field(default=0, ge=0)
    fixed_amount: Decimal = Field(default=0, ge=0)
    unit_amount: Decimal = Field(default=0, ge=0)
    percent_rate: Decimal = Field(default=0, ge=0, le=100)
    minimum_amount: Decimal | None = Field(default=None, ge=0)
    priority: int = Field(default=100, ge=0)
    description: str | None = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def validate_range(self):
        if self.max_value is not None and self.min_value is not None and self.max_value < self.min_value:
            raise ValueError("max_value cannot be less than min_value")
        return self


class PricingRuleResponse(PricingRuleCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool


class ShippingCostInput(BaseModel):
    company_id: int = Field(gt=0)
    carrier_id: int = Field(gt=0)
    calculation_date: date
    zone_code: str | None = None
    weight_kg: Decimal = Field(default=0, ge=0)
    pieces: Decimal = Field(default=1, gt=0)
    order_value: Decimal = Field(default=0, ge=0)
    cod_amount: Decimal = Field(default=0, ge=0)
    cod_collected: Decimal = Field(default=0, ge=0)
    card_amount: Decimal = Field(default=0, ge=0)
    remote_area: bool = False
    shipment_status: Literal["pending", "picked_up", "in_transit", "out_for_delivery", "delivered", "returned", "cancelled"] = "pending"
    storage_days: Decimal = Field(default=0, ge=0)


class ShippingCostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    profile_id: int
    profile_name: str
    base_shipping: Decimal
    cod_fee: Decimal
    cod_collected_fee: Decimal
    card_fee: Decimal
    surcharge_remote: Decimal
    surcharge_rto: Decimal
    surcharge_exchange: Decimal
    storage_fee: Decimal
    other_fees: Decimal
    minimum_adjustment: Decimal
    total_cost: Decimal
    breakdown: list[dict]
