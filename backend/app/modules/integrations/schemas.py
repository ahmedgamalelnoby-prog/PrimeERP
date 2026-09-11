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
