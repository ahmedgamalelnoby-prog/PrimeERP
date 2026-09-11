from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class SettlementLineCreate(BaseModel):
    shipment_id: int = Field(gt=0)
    collected_amount: Decimal = Field(ge=0)
    carrier_fee: Decimal = Field(default=Decimal("0"), ge=0)


class SettlementBatchCreate(BaseModel):
    company_id: int = Field(gt=0)
    carrier_id: int = Field(gt=0)
    reference: str = Field(min_length=1, max_length=100)
    settlement_date: date
    lines: list[SettlementLineCreate] = Field(min_length=1)
    notes: str | None = None


class SettlementLineResponse(BaseModel):
    id: int
    batch_id: int
    shipment_id: int
    expected_amount: Decimal
    collected_amount: Decimal
    carrier_fee: Decimal
    net_amount: Decimal
    variance: Decimal
    reconciled: bool

    model_config = {"from_attributes": True}


class SettlementBatchResponse(BaseModel):
    id: int
    company_id: int
    carrier_id: int
    reference: str
    settlement_date: date
    gross_amount: Decimal
    carrier_fees: Decimal
    net_amount: Decimal
    status: str
    notes: str | None

    model_config = {"from_attributes": True}
