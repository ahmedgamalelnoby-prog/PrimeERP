from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .constants import (
    FeatureCategory,
    FeatureStatus,
    FeatureType,
    FeatureValueType,
)


FEATURE_CODE_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$"
)


class FeatureBase(BaseModel):
    code: str = Field(
        min_length=2,
        max_length=150,
        examples=["accounting.journal_entries"],
    )

    name: str = Field(
        min_length=2,
        max_length=150,
    )

    name_ar: str | None = Field(
        default=None,
        max_length=150,
    )

    display_name: str | None = Field(
        default=None,
        max_length=150,
    )

    description: str | None = None

    category: FeatureCategory = FeatureCategory.SYSTEM

    feature_type: FeatureType = FeatureType.FUNCTION

    value_type: FeatureValueType = FeatureValueType.BOOLEAN

    default_value: str | None = Field(
        default=None,
        max_length=255,
    )

    icon: str | None = Field(
        default=None,
        max_length=100,
    )

    sort_order: int = Field(
        default=0,
        ge=0,
    )

    is_core: bool = False
    is_billable: bool = True
    is_public: bool = True

    status: FeatureStatus = FeatureStatus.ACTIVE

    parent_id: int | None = Field(
        default=None,
        gt=0,
    )

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        normalized_value = value.strip().lower()

        if not FEATURE_CODE_PATTERN.fullmatch(normalized_value):
            raise ValueError(
                "Feature code must use lowercase letters, numbers, "
                "underscores and dots only. "
                "Example: accounting.journal_entries"
            )

        return normalized_value

    @field_validator("name", "name_ar", "display_name")
    @classmethod
    def normalize_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized_value = value.strip()

        if not normalized_value:
            return None

        return normalized_value


class FeatureCreate(FeatureBase):
    pass


class FeatureUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    name_ar: str | None = Field(
        default=None,
        max_length=150,
    )

    display_name: str | None = Field(
        default=None,
        max_length=150,
    )

    description: str | None = None
    category: FeatureCategory | None = None
    feature_type: FeatureType | None = None
    value_type: FeatureValueType | None = None

    default_value: str | None = Field(
        default=None,
        max_length=255,
    )

    icon: str | None = Field(
        default=None,
        max_length=100,
    )

    sort_order: int | None = Field(
        default=None,
        ge=0,
    )

    is_core: bool | None = None
    is_billable: bool | None = None
    is_public: bool | None = None
    status: FeatureStatus | None = None

    parent_id: int | None = Field(
        default=None,
        gt=0,
    )


class FeatureRead(FeatureBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: str

    created_at: datetime
    updated_at: datetime

    created_by: int | None = None
    updated_by: int | None = None

    is_deleted: bool = False
    deleted_at: datetime | None = None
    deleted_by: int | None = None


class FeatureListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: str
    code: str
    name: str
    name_ar: str | None
    category: str
    feature_type: str
    value_type: str
    status: str
    is_core: bool
    is_billable: bool
    sort_order: int


class FeatureValueValidationRequest(BaseModel):
    value_type: FeatureValueType
    value: Any


class FeatureValueValidationResponse(BaseModel):
    is_valid: bool
    normalized_value: str | None = None
    error: str | None = None