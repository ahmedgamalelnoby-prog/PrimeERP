from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class ProviderCreate(BaseModel):
    tenant_id: int
    code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=150)
    country_code: str = Field(default="EG", min_length=2, max_length=2)
    website: str | None = None
    api_enabled: bool = False
    notes: str | None = None

class ProviderRead(ProviderCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    active: bool

class PaymentProfileCreate(BaseModel):
    provider_id: int
    name: str
    payment_method: str = "prepaid"
    billing_cycle: str = "per_shipment"
    cod_enabled: bool = False
    cod_fee_type: str | None = None
    cod_fee_value: Decimal | None = None
    settlement_cycle: str = "contractual"
    settlement_percent: Decimal | None = None
    currency_code: str = "EGP"
    notes: str | None = None

class PaymentProfileRead(PaymentProfileCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    active: bool

class ShipmentCreate(BaseModel):
    tenant_id: int
    company_id: int | None = None
    branch_id: int | None = None
    source_module: str | None = None
    source_entity: str | None = None
    source_id: int | None = None
    provider_id: int
    service_id: int | None = None
    reference: str = Field(min_length=1, max_length=100)
    payment_method: str = "prepaid"
    cod_amount: Decimal = Decimal("0")
    shipping_fee: Decimal = Decimal("0")
    cod_fee: Decimal = Decimal("0")
    other_fee: Decimal = Decimal("0")
    weight_kg: Decimal | None = None
    volumetric_weight_kg: Decimal | None = None
    customer_name: str
    customer_phone: str | None = None
    address: str | None = None
    city: str | None = None
    country_code: str = "EG"
    notes: str | None = None

class ShipmentRead(ShipmentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    transaction_id: int | None
    external_id: str | None
    tracking_number: str | None
    status: str
    shipped_at: datetime | None
    delivered_at: datetime | None
    returned_at: datetime | None

class ShipmentStatusUpdate(BaseModel):
    status: str = Field(min_length=2, max_length=30)
    description: str | None = None
    event_code: str | None = None
    tracking_number: str | None = None

class ShipmentExecuteRequest(BaseModel):
    connection_id: int
    provider_payload: dict | None = None

class ShipmentExecuteResponse(BaseModel):
    shipment_id: int
    provider: str
    status: str
    tracking_number: str | None
    external_id: str | None
    raw: dict

class ShipmentTrackResponse(BaseModel):
    shipment_id: int
    provider: str
    tracking_number: str
    raw: dict
