from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


BillingCycle = Literal["monthly", "quarterly", "semi_annual", "yearly"]


class SubscriptionCreate(BaseModel):
    tenant_id: int = Field(gt=0)
    plan_id: int = Field(gt=0)
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    trial_ends_at: Optional[datetime] = None
    billing_cycle: BillingCycle = "monthly"
    auto_renew: bool = False
    custom_max_users: Optional[int] = Field(default=None, ge=1)
    custom_max_companies: Optional[int] = Field(default=None, ge=1)
    custom_max_branches: Optional[int] = Field(default=None, ge=1)
    notes: Optional[str] = None


class SubscriptionUpdate(BaseModel):
    plan_id: Optional[int] = Field(default=None, gt=0)
    billing_cycle: Optional[BillingCycle] = None
    ends_at: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None
    auto_renew: Optional[bool] = None
    custom_max_users: Optional[int] = Field(default=None, ge=1)
    custom_max_companies: Optional[int] = Field(default=None, ge=1)
    custom_max_branches: Optional[int] = Field(default=None, ge=1)
    notes: Optional[str] = None


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    plan_id: int
    status: str
    billing_cycle: str
    starts_at: datetime
    ends_at: Optional[datetime]
    trial_ends_at: Optional[datetime]
    next_billing_date: Optional[datetime]
    cancelled_at: Optional[datetime]
    auto_renew: bool = Field(
        validation_alias="is_auto_renew",
        serialization_alias="auto_renew",
    )
    custom_max_users: Optional[int]
    custom_max_companies: Optional[int]
    custom_max_branches: Optional[int]
    notes: Optional[str]
