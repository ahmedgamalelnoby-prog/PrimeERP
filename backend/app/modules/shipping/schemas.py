from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator


PaymentMethod = str


class CarrierCreate(BaseModel):
    company_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=150)
    api_base_url: str | None = Field(default=None, max_length=500)
    settlement_account_id: int | None = Field(default=None, gt=0)
    cash_account_id: int | None = Field(default=None, gt=0)
    fee_account_id: int | None = Field(default=None, gt=0)
    settlement_journal_id: int | None = Field(default=None, gt=0)
    branch_id: int | None = Field(default=None, gt=0)

    @field_validator("code", "name", mode="before")
    @classmethod
    def clean_required(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Value cannot be empty")
        return value.strip()


class CarrierResponse(CarrierCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool


class MethodCreate(BaseModel):
    carrier_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=150)
    payment_method: str = Field(min_length=1, max_length=20)
    payment_account_id: int | None = Field(default=None, gt=0)
    base_fee: Decimal = Field(default=0, ge=0)
    cod_fee_percent: Decimal = Field(default=0, ge=0, le=100)
    estimated_days: int = Field(default=1, gt=0)

    @field_validator("name", "payment_method", mode="before")
    @classmethod
    def clean_required(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Value cannot be empty")
        return value.strip().lower() if value != "name" else value.strip()


class MethodResponse(MethodCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ShipmentCreate(BaseModel):
    company_id: int = Field(gt=0)
    carrier_id: int = Field(gt=0)
    method_id: int = Field(gt=0)
    sales_document_id: int | None = Field(default=None, gt=0)
    tracking_no: str = Field(min_length=1, max_length=120)
    cod_amount: Decimal = Field(default=0, ge=0)
    shipping_fee: Decimal = Field(default=0, ge=0)
    customer_name: str = Field(min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=40)
    address: str | None = Field(default=None, max_length=1000)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("tracking_no", "customer_name", "phone", "address", "notes", mode="before")
    @classmethod
    def clean_text(cls, value):
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Value cannot be empty")
        return value.strip()


class ShipmentResponse(ShipmentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str


class SettlementLineCreate(BaseModel):
    shipment_id: int = Field(gt=0)
    collected_amount: Decimal = Field(ge=0)
    carrier_fee: Decimal = Field(default=0, ge=0)


class SettlementBatchCreate(BaseModel):
    company_id: int = Field(gt=0)
    carrier_id: int = Field(gt=0)
    reference: str = Field(min_length=1, max_length=100)
    settlement_date: date
    lines: list[SettlementLineCreate] = Field(min_length=1)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("reference", "notes", mode="before")
    @classmethod
    def clean_text(cls, value):
        if value is None:
            return None
        value = value.strip()
        return value or None


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
    lines: list[SettlementLineResponse] = Field(default_factory=list)
