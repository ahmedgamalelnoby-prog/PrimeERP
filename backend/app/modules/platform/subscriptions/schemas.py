from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.platform.subscriptions.constants import SubscriptionStatus


class SubscriptionCreate(BaseModel):
    tenant_id: int = Field(gt=0)
    plan_id: int = Field(gt=0)
    starts_at: Optional[datetime] = None
    trial_ends_at: Optional[datetime] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    quantity: int = Field(default=1, ge=1)
    price: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = Field(default="EGP", min_length=3, max_length=10)
    auto_renew: bool = True
    external_reference: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = None


class SubscriptionUpdate(BaseModel):
    plan_id: Optional[int] = Field(default=None, gt=0)
    auto_renew: Optional[bool] = None
    quantity: Optional[int] = Field(default=None, ge=1)
    price: Optional[Decimal] = Field(default=None, ge=0)
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    notes: Optional[str] = None


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    plan_id: int
    status: SubscriptionStatus
    starts_at: datetime
    trial_ends_at: Optional[datetime]
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    cancelled_at: Optional[datetime]
    cancellation_reason: Optional[str]
    auto_renew: bool
    quantity: int
    price: Decimal
    currency: str
    external_reference: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
