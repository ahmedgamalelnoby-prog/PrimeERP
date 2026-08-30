from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.platform.plans.constants import (
    BillingCycle,
    PlanCurrency,
    PlanStatus,
    PlanType,
)


class PlanBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=100)
    name_ar: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None

    monthly_price: Decimal = Decimal("0.00")
    yearly_price: Decimal = Decimal("0.00")

    currency: PlanCurrency = PlanCurrency.EGP
    billing_cycle: BillingCycle = BillingCycle.MONTHLY

    trial_days: int = 14
    grace_period_days: int = 7

    is_default: bool = False
    is_public: bool = True
    is_free: bool = False
    is_custom: bool = False

    status: PlanStatus = PlanStatus.DRAFT
    plan_type: PlanType = PlanType.STANDARD

    sort_order: int = 0


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    code: Optional[str] = Field(default=None, min_length=2, max_length=50)
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    name_ar: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None

    monthly_price: Optional[Decimal] = None
    yearly_price: Optional[Decimal] = None

    currency: Optional[PlanCurrency] = None
    billing_cycle: Optional[BillingCycle] = None

    trial_days: Optional[int] = None
    grace_period_days: Optional[int] = None

    is_default: Optional[bool] = None
    is_public: Optional[bool] = None
    is_free: Optional[bool] = None
    is_custom: Optional[bool] = None

    status: Optional[PlanStatus] = None
    plan_type: Optional[PlanType] = None

    sort_order: Optional[int] = None


class PlanResponse(PlanBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: str
    version: int

    effective_from: Optional[str] = None
    effective_to: Optional[str] = None

    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PlanListResponse(BaseModel):
    items: list[PlanResponse]
    total: int
    page: int
    page_size: int
    pages: int