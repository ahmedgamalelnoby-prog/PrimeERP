from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class CarrierCreate(BaseModel):
    company_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=150)
    api_base_url: str | None = None
    settlement_account_id: int | None = Field(default=None, gt=0)
    cash_account_id: int | None = Field(default=None, gt=0)
    fee_account_id: int | None = Field(default=None, gt=0)
    settlement_journal_id: int | None = Field(default=None, gt=0)
    branch_id: int | None = Field(default=None, gt=0)


class CarrierResponse(CarrierCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool


class MethodCreate(BaseModel):
    carrier_id: int = Field(gt=0)
    name: str
    payment_method: str
    payment_account_id: int | None = Field(default=None, gt=0)
    base_fee: Decimal = Field(default=0, ge=0)
    cod_fee_percent: Decimal = Field(default=0, ge=0, le=100)
    estimated_days: int = Field(default=1, gt=0)


class MethodResponse(MethodCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ShipmentCreate(BaseModel):
    company_id: int = Field(gt=0)
    carrier_id: int = Field(gt=0)
    method_id: int = Field(gt=0)
    sales_document_id: int | None = Field(default=None, gt=0)
    tracking_no: str
    order_date: date | None = None
    shipment_date: date | None = None
    zone_code: str | None = None
    weight_kg: Decimal = Field(default=0, ge=0)
    pieces: Decimal = Field(default=1, gt=0)
    order_value: Decimal = Field(default=0, ge=0)
    cod_amount: Decimal = Field(default=0, ge=0)
    cod_collected: Decimal = Field(default=0, ge=0)
    card_amount: Decimal = Field(default=0, ge=0)
    remote_area: bool = False
    storage_days: Decimal = Field(default=0, ge=0)
    exchange_requested: bool = False
    shipping_fee: Decimal = Field(default=0, ge=0)
    customer_shipping_fee: Decimal = Field(default=0, ge=0)
    customer_name: str
    phone: str | None = None
    address: str | None = None
    notes: str | None = None


class ShipmentResponse(ShipmentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str


class SettlementLineCreate(BaseModel):
    shipment_id: int = Field(gt=0)
    collected_amount: Decimal = Field(ge=0)
    carrier_fee: Decimal = Field(default=0, ge=0)
    cod_commission: Decimal = Field(default=0, ge=0)
    withdrawal_fee: Decimal = Field(default=0, ge=0)
    other_fee: Decimal = Field(default=0, ge=0)


class SettlementBatchCreate(BaseModel):
    company_id: int = Field(gt=0)
    carrier_id: int = Field(gt=0)
    reference: str = Field(min_length=1, max_length=100)
    settlement_date: date
    lines: list[SettlementLineCreate] = Field(min_length=1)
    notes: str | None = None


class SettlementLineResponse(SettlementLineCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    batch_id: int
    expected_amount: Decimal
    net_amount: Decimal
    variance: Decimal
    reconciled: bool


class SettlementBatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
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
    lines: list[SettlementLineResponse] = []
