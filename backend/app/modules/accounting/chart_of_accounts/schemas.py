from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


def validate_numeric_code(
    value: str,
    length: int,
    field_name: str,
) -> str:
    value = value.strip()

    if not value.isdigit():
        raise ValueError(
            f"{field_name} must contain numbers only"
        )

    if len(value) != length:
        raise ValueError(
            f"{field_name} must be exactly "
            f"{length} digits"
        )

    return value


class DepartmentBase(BaseModel):
    company_id: int

    code: str

    name_ar: str = Field(
        min_length=2,
        max_length=150,
    )

    name_en: Optional[str] = Field(
        default=None,
        max_length=150,
    )

    description: Optional[str] = None

    is_active: bool = True

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        return validate_numeric_code(
            value,
            2,
            "Department code",
        )


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    code: Optional[str] = None

    name_ar: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    name_en: Optional[str] = Field(
        default=None,
        max_length=150,
    )

    description: Optional[str] = None

    is_active: Optional[bool] = None

    @field_validator("code")
    @classmethod
    def validate_code(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return value

        return validate_numeric_code(
            value,
            2,
            "Department code",
        )


class DepartmentResponse(DepartmentBase):
    id: int

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class CostCenterBase(BaseModel):
    company_id: int

    department_id: int

    branch_id: Optional[int] = None

    code: str

    name_ar: str = Field(
        min_length=2,
        max_length=150,
    )

    name_en: Optional[str] = Field(
        default=None,
        max_length=150,
    )

    description: Optional[str] = None

    is_active: bool = True

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        return validate_numeric_code(
            value,
            3,
            "Cost center code",
        )


class CostCenterCreate(CostCenterBase):
    pass


class CostCenterUpdate(BaseModel):
    department_id: Optional[int] = None

    branch_id: Optional[int] = None

    code: Optional[str] = None

    name_ar: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    name_en: Optional[str] = Field(
        default=None,
        max_length=150,
    )

    description: Optional[str] = None

    is_active: Optional[bool] = None

    @field_validator("code")
    @classmethod
    def validate_code(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return value

        return validate_numeric_code(
            value,
            3,
            "Cost center code",
        )


class CostCenterResponse(CostCenterBase):
    id: int

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class NaturalAccountBase(BaseModel):
    company_id: int

    parent_id: Optional[int] = None

    code: str

    name_ar: str = Field(
        min_length=2,
        max_length=200,
    )

    name_en: Optional[str] = Field(
        default=None,
        max_length=200,
    )

    financial_statement: str

    account_category: str

    normal_balance: str

    level: int = Field(
        default=1,
        ge=1,
        le=20,
    )

    is_posting: bool = True

    is_control_account: bool = False

    requires_cost_center: bool = True

    currency_code: str = Field(
        default="EGP",
        min_length=3,
        max_length=3,
    )

    description: Optional[str] = None

    is_active: bool = True

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        return validate_numeric_code(
            value,
            3,
            "Natural account code",
        )

    @field_validator("financial_statement")
    @classmethod
    def validate_statement(
        cls,
        value: str,
    ) -> str:
        allowed = {
            "balance_sheet",
            "profit_and_loss",
        }

        if value not in allowed:
            raise ValueError(
                "Financial statement must be "
                "balance_sheet or profit_and_loss"
            )

        return value

    @field_validator("normal_balance")
    @classmethod
    def validate_balance(
        cls,
        value: str,
    ) -> str:
        allowed = {
            "debit",
            "credit",
        }

        if value not in allowed:
            raise ValueError(
                "Normal balance must be "
                "debit or credit"
            )

        return value


class NaturalAccountCreate(
    NaturalAccountBase
):
    pass


class NaturalAccountUpdate(BaseModel):
    parent_id: Optional[int] = None

    code: Optional[str] = None

    name_ar: Optional[str] = None

    name_en: Optional[str] = None

    financial_statement: Optional[str] = None

    account_category: Optional[str] = None

    normal_balance: Optional[str] = None

    level: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
    )

    is_posting: Optional[bool] = None

    is_control_account: Optional[bool] = None

    requires_cost_center: Optional[bool] = None

    currency_code: Optional[str] = None

    description: Optional[str] = None

    is_active: Optional[bool] = None


class NaturalAccountResponse(
    NaturalAccountBase
):
    id: int

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class AccountCombinationCreate(BaseModel):
    company_id: int

    department_id: int

    cost_center_id: int

    natural_account_id: int

    name_ar: Optional[str] = None

    name_en: Optional[str] = None

    opening_debit: Decimal = Decimal("0")

    opening_credit: Decimal = Decimal("0")

    is_active: bool = True


class AccountCombinationResponse(BaseModel):
    id: int

    company_id: int

    department_id: int

    cost_center_id: int

    natural_account_id: int

    code: str

    name_ar: str

    name_en: Optional[str] = None

    opening_debit: Decimal

    opening_credit: Decimal

    is_active: bool

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class AccountingSettingsResponse(BaseModel):
    id: int

    company_id: int

    code_format: str

    code_length: int

    department_length: int

    cost_center_length: int

    natural_account_length: int

    base_currency: str

    allow_manual_code: bool

    allow_duplicate_account_names: bool

    require_cost_center: bool

    model_config = ConfigDict(
        from_attributes=True
    )