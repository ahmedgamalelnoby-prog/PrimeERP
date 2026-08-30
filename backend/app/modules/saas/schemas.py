import re

from datetime import datetime
from typing import Literal, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


BusinessType = Literal[
    "restaurant",
    "cafe",
    "retail",
    "fashion",
    "perfume",
    "supermarket",
    "pharmacy",
    "manufacturing",
    "services",
    "other",
]

LanguageCode = Literal["ar", "en"]


USERNAME_PATTERN = re.compile(
    r"^[A-Za-z0-9_-]+$"
)


class TenantRegistrationRequest(BaseModel):
    business_name: str = Field(
        min_length=2,
        max_length=200,
    )

    business_type: BusinessType = "other"

    owner_name: str = Field(
        min_length=2,
        max_length=150,
    )

    email: EmailStr

    phone: Optional[str] = Field(
        default=None,
        max_length=30,
    )

    username: str = Field(
        min_length=3,
        max_length=50,
    )

    password: str = Field(
        min_length=8,
        max_length=72,
    )

    country_code: str = Field(
        default="EG",
        min_length=2,
        max_length=2,
    )

    language: LanguageCode = "ar"

    company_name: Optional[str] = Field(
        default=None,
        max_length=150,
    )

    branch_name: Optional[str] = Field(
        default=None,
        max_length=150,
    )

    @field_validator(
        "business_name",
        "owner_name",
    )
    @classmethod
    def clean_required_text(
        cls,
        value: str,
    ) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError(
                "Value cannot be empty"
            )

        return cleaned_value

    @field_validator(
        "company_name",
        "branch_name",
    )
    @classmethod
    def clean_optional_text(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return None

        cleaned_value = value.strip()

        return cleaned_value or None

    @field_validator(
        "username",
        mode="before",
    )
    @classmethod
    def normalize_username(
        cls,
        value: object,
    ) -> str:
        if not isinstance(value, str):
            raise ValueError(
                "Username must be a string"
            )

        normalized_username = (
            value
            .strip()
            .lower()
            .replace(" ", "_")
        )

        return normalized_username

    @field_validator("username")
    @classmethod
    def validate_username(
        cls,
        value: str,
    ) -> str:
        if not USERNAME_PATTERN.fullmatch(
            value
        ):
            raise ValueError(
                "Username may contain English letters, "
                "numbers, underscores and hyphens only"
            )

        return value

    @field_validator("password")
    @classmethod
    def validate_password(
        cls,
        value: str,
    ) -> str:
        password_bytes = value.encode(
            "utf-8"
        )

        if len(password_bytes) > 72:
            raise ValueError(
                "Password cannot exceed 72 bytes"
            )

        return value

    @field_validator("phone")
    @classmethod
    def clean_phone(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return None

        cleaned_value = value.strip()

        return cleaned_value or None

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(
        cls,
        value: str,
    ) -> str:
        return value.strip().upper()


class RegisteredUserResponse(BaseModel):
    id: int
    tenant_id: int
    username: str
    email: str
    full_name: Optional[str]
    preferred_language: str
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True
    )


class RegisteredTenantResponse(BaseModel):
    id: int
    name: str
    slug: str
    business_type: str
    status: str
    is_trial: bool
    trial_started_at: Optional[datetime]
    trial_ends_at: Optional[datetime]
    default_language: str
    currency_code: str

    model_config = ConfigDict(
        from_attributes=True
    )


class RegisteredCompanyResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    code: Optional[str]

    model_config = ConfigDict(
        from_attributes=True
    )


class RegisteredBranchResponse(BaseModel):
    id: int
    tenant_id: int
    company_id: int
    name: str
    code: Optional[str]

    model_config = ConfigDict(
        from_attributes=True
    )


class TenantRegistrationResponse(BaseModel):
    message: str
    tenant: RegisteredTenantResponse
    company: RegisteredCompanyResponse
    branch: RegisteredBranchResponse
    user: RegisteredUserResponse
    subscription_status: str
    plan_code: str
    enabled_modules: list[str]
    trial_ends_at: Optional[datetime]