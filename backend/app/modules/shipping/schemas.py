from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class CarrierCreate(BaseModel):
    company_id: int = Field(gt=0)
    code: str
    name: str
    api_base_url: str | None = None


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
    sales_document_id: int | None = None
    tracking_no: str
    cod_amount: Decimal = Field(default=0, ge=0)
    shipping_fee: Decimal = Field(default=0, ge=0)
    customer_name: str
    phone: str | None = None
    address: str | None = None
    notes: str | None = None


class ShipmentResponse(ShipmentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
