from datetime import date, datetime
from typing import Literal, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


FiscalYearStatus = Literal[
    "draft",
    "open",
    "closing",
    "closed",
]

AccountingPeriodStatus = Literal[
    "draft",
    "open",
    "closing",
    "closed",
    "locked",
]


class FiscalYearCreate(BaseModel):
    company_id: int = Field(
        gt=0,
    )

    code: str = Field(
        min_length=2,
        max_length=30,
    )

    name_ar: str = Field(
        min_length=2,
        max_length=150,
    )

    name_en: str = Field(
        min_length=2,
        max_length=150,
    )

    start_date: date

    end_date: date

    create_monthly_periods: bool = True

    adjustment_period: bool = False

    @model_validator(mode="after")
    def validate_dates(
        self,
    ):
        if self.end_date < self.start_date:
            raise ValueError(
                "End date must be after start date"
            )

        return self


class FiscalYearUpdate(BaseModel):
    code: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=30,
    )

    name_ar: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    name_en: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    start_date: Optional[date] = None

    end_date: Optional[date] = None

    is_adjustment_period_enabled: Optional[
        bool
    ] = None

    @model_validator(mode="after")
    def validate_dates(
        self,
    ):
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError(
                "End date must be after start date"
            )

        return self


class AccountingPeriodCreate(BaseModel):
    period_number: int = Field(
        gt=0,
        le=99,
    )

    code: str = Field(
        min_length=2,
        max_length=30,
    )

    name_ar: str = Field(
        min_length=2,
        max_length=150,
    )

    name_en: str = Field(
        min_length=2,
        max_length=150,
    )

    start_date: date

    end_date: date

    is_adjustment: bool = False

    @model_validator(mode="after")
    def validate_dates(
        self,
    ):
        if self.end_date < self.start_date:
            raise ValueError(
                "End date must be after start date"
            )

        return self


class AccountingPeriodResponse(BaseModel):
    id: int

    tenant_id: int

    company_id: int

    fiscal_year_id: int

    period_number: int

    code: str

    name_ar: str

    name_en: str

    start_date: date

    end_date: date

    status: str

    is_adjustment: bool

    allow_posting: bool

    opened_by: Optional[int]

    opened_at: Optional[datetime]

    closed_by: Optional[int]

    closed_at: Optional[datetime]

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class FiscalYearResponse(BaseModel):
    id: int

    tenant_id: int

    company_id: int

    code: str

    name_ar: str

    name_en: str

    start_date: date

    end_date: date

    status: str

    is_current: bool

    is_adjustment_period_enabled: bool

    opened_by: Optional[int]

    opened_at: Optional[datetime]

    closed_by: Optional[int]

    closed_at: Optional[datetime]

    created_at: datetime

    updated_at: datetime

    periods: list[
        AccountingPeriodResponse
    ] = []

    model_config = ConfigDict(
        from_attributes=True
    )


class FiscalYearActionRequest(BaseModel):
    reason: Optional[str] = Field(
        default=None,
        max_length=1000,
    )