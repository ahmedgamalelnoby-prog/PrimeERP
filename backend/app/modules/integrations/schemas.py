from datetime import datetime

from pydantic import BaseModel, Field


class ConnectionCreate(BaseModel):
    company_id: int = Field(gt=0)
    provider: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=120)
    base_url: str | None = None
    credential_ref: str | None = Field(default=None, max_length=200)
    webhook_secret_env: str | None = Field(default=None, min_length=1, max_length=200)


class ConnectionResponse(BaseModel):
    id: int
    company_id: int
    provider: str
    name: str
    base_url: str | None
    credential_ref: str | None
    webhook_secret_env: str | None
    is_active: bool
    last_sync_at: datetime | None

    class Config:
        from_attributes = True


class WebhookEventCreate(BaseModel):
    external_event_id: str = Field(min_length=1, max_length=160)
    event_type: str = Field(min_length=1, max_length=100)
    payload: dict


class SallaSyncSettingsCreate(BaseModel):
    warehouse_id: int | None = Field(default=None, gt=0)
    default_tax_rate_id: int | None = Field(default=None, gt=0)
    customer_code_prefix: str = Field(default="SALLA-C-", min_length=1, max_length=20)
    product_code_prefix: str = Field(default="SALLA-P-", min_length=1, max_length=20)
    import_paid_orders: bool = False
    auto_fulfill_orders: bool = False
    active: bool = True
    notes: str | None = Field(default=None, max_length=2000)


class SallaSyncSettingsResponse(SallaSyncSettingsCreate):
    id: int
    connection_id: int

    class Config:
        from_attributes = True
