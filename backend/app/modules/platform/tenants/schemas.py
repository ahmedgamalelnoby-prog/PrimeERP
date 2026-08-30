from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from .constants import (
    BusinessType,
    DEFAULT_COUNTRY_CODE,
    DEFAULT_CURRENCY,
    DEFAULT_LANGUAGE,
    DEFAULT_LOCALE,
    DEFAULT_TIMEZONE,
    TenantStatus,
)
from .validators import (
    normalize_country_code,
    normalize_currency_code,
    normalize_email,
    normalize_tenant_slug,
)


class TenantBase(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(min_length=2, max_length=100)

    business_type: BusinessType = BusinessType.GENERAL

    owner_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)

    country_code: str = Field(
        default=DEFAULT_COUNTRY_CODE,
        min_length=2,
        max_length=2,
    )

    default_language: str = Field(
        default=DEFAULT_LANGUAGE,
        min_length=2,
        max_length=5,
    )

    default_locale: str = Field(
        default=DEFAULT_LOCALE,
        min_length=2,
        max_length=10,
    )

    timezone: str = Field(
        default=DEFAULT_TIMEZONE,
        min_length=1,
        max_length=50,
    )

    currency_code: str = Field(
        default=DEFAULT_CURRENCY,
        min_length=3,
        max_length=3,
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        return normalize_tenant_slug(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: EmailStr) -> str:
        return normalize_email(str(value))

    @field_validator("country_code")
    @classmethod
    def validate_country_code(cls, value: str) -> str:
        return normalize_country_code(value)

    @field_validator("currency_code")
    @classmethod
    def validate_currency_code(cls, value: str) -> str:
        return normalize_currency_code(value)


class TenantCreate(TenantBase):
    is_trial: bool = True
    trial_started_at: datetime | None = None
    trial_ends_at: datetime | None = None

    @model_validator(mode="after")
    def validate_trial_dates(self) -> "TenantCreate":
        if not self.is_trial:
            self.trial_started_at = None
            self.trial_ends_at = None
            return self

        if (
            self.trial_started_at
            and self.trial_ends_at
            and self.trial_ends_at <= self.trial_started_at
        ):
            raise ValueError(
                "Trial end date must be later than trial start date."
            )

        return self


class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    slug: str | None = Field(default=None, min_length=2, max_length=100)

    business_type: BusinessType | None = None

    owner_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)

    country_code: str | None = Field(
        default=None,
        min_length=2,
        max_length=2,
    )

    default_language: str | None = Field(
        default=None,
        min_length=2,
        max_length=5,
    )

    default_locale: str | None = Field(
        default=None,
        min_length=2,
        max_length=10,
    )

    timezone: str | None = Field(default=None, max_length=50)

    currency_code: str | None = Field(
        default=None,
        min_length=3,
        max_length=3,
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str | None) -> str | None:
        if value is None:
            return None

        return normalize_tenant_slug(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: EmailStr | None) -> str | None:
        if value is None:
            return None

        return normalize_email(str(value))

    @field_validator("country_code")
    @classmethod
    def validate_country_code(cls, value: str | None) -> str | None:
        if value is None:
            return None

        return normalize_country_code(value)

    @field_validator("currency_code")
    @classmethod
    def validate_currency_code(cls, value: str | None) -> str | None:
        if value is None:
            return None

        return normalize_currency_code(value)


class TenantSuspendRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)


class TenantRead(TenantBase):
    model_config = ConfigDict(from_attributes=True)

    id: int

    status: TenantStatus
    is_trial: bool

    trial_started_at: datetime | None
    trial_ends_at: datetime | None

    is_active: bool

    suspended_at: datetime | None
    suspension_reason: str | None

    created_at: datetime
    updated_at: datetime


class TenantListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    business_type: str
    owner_name: str
    email: EmailStr
    status: str
    is_trial: bool
    is_active: bool
    created_at: datetime


class TenantListResponse(BaseModel):
    items: list[TenantListItem]
    total: int
    page: int
    page_size: int
    pages: int