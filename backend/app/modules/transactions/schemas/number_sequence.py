from datetime import datetime
from typing import Literal, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


ResetPeriod = Literal[
    "never",
    "yearly",
    "monthly",
]


class NumberSequenceBase(BaseModel):
    tenant_id: int = Field(
        gt=0,
    )

    company_id: int = Field(
        gt=0,
    )

    branch_id: int = Field(
        gt=0,
    )

    sequence_key: str = Field(
        min_length=2,
        max_length=50,
    )

    prefix: str = Field(
        default="TRX",
        min_length=1,
        max_length=20,
    )

    format_pattern: str = Field(
        default=(
            "{PREFIX}-{YEAR}-"
            "{BRANCH}-{SEQ}"
        ),
        min_length=5,
        max_length=150,
    )

    padding: int = Field(
        default=8,
        ge=1,
        le=20,
    )

    reset_period: ResetPeriod = "yearly"

    is_active: bool = True

    @field_validator(
        "sequence_key",
        "prefix",
    )
    @classmethod
    def normalize_codes(
        cls,
        value: str,
    ) -> str:
        cleaned = value.strip().upper()

        if not cleaned:
            raise ValueError(
                "Value cannot be empty"
            )

        return cleaned

    @field_validator("format_pattern")
    @classmethod
    def validate_pattern(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if "{SEQ}" not in value:
            raise ValueError(
                "Format pattern must contain {SEQ}"
            )

        supported_tokens = {
            "{PREFIX}",
            "{YEAR}",
            "{YY}",
            "{MONTH}",
            "{COMPANY}",
            "{BRANCH}",
            "{SEQ}",
        }

        remaining_value = value

        for token in supported_tokens:
            remaining_value = (
                remaining_value.replace(
                    token,
                    "",
                )
            )

        if "{" in remaining_value:
            raise ValueError(
                "Format pattern contains "
                "an unsupported token"
            )

        return value


class NumberSequenceCreate(
    NumberSequenceBase
):
    current_value: int = Field(
        default=0,
        ge=0,
    )


class NumberSequenceUpdate(BaseModel):
    prefix: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=20,
    )

    format_pattern: Optional[str] = Field(
        default=None,
        min_length=5,
        max_length=150,
    )

    padding: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
    )

    reset_period: Optional[
        ResetPeriod
    ] = None

    is_active: Optional[bool] = None

    @field_validator("prefix")
    @classmethod
    def normalize_prefix(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return None

        return value.strip().upper()

    @field_validator("format_pattern")
    @classmethod
    def validate_pattern(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return None

        value = value.strip()

        if "{SEQ}" not in value:
            raise ValueError(
                "Format pattern must contain {SEQ}"
            )

        return value


class NumberSequenceResponse(
    NumberSequenceBase
):
    id: int

    current_value: int

    last_reset_year: Optional[int]

    last_reset_month: Optional[int]

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class GenerateNumberRequest(BaseModel):
    tenant_id: int = Field(
        gt=0,
    )

    company_id: int = Field(
        gt=0,
    )

    branch_id: int = Field(
        gt=0,
    )

    sequence_key: str = Field(
        min_length=2,
        max_length=50,
    )

    @field_validator("sequence_key")
    @classmethod
    def normalize_sequence_key(
        cls,
        value: str,
    ) -> str:
        return value.strip().upper()


class GeneratedNumberResponse(BaseModel):
    sequence_id: int

    sequence_key: str

    generated_number: str

    sequence_value: int

    generated_at: datetime