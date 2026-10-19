from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class JournalLineInput(BaseModel):
    account_combination_id: int = Field(gt=0)
    debit: Decimal = Field(default=Decimal("0"), ge=0)
    credit: Decimal = Field(default=Decimal("0"), ge=0)
    department_id: int | None = Field(default=None, gt=0)
    cost_center_id: int | None = Field(default=None, gt=0)
    description: str | None = None
    reference: str | None = None


class JournalEntryCreate(BaseModel):
    company_id: int = Field(gt=0)
    branch_id: int = Field(gt=0)
    journal_id: int = Field(gt=0)
    fiscal_year_id: int = Field(gt=0)
    period_id: int = Field(gt=0)
    entry_number: str = Field(min_length=1, max_length=50)
    entry_date: date
    description: str = Field(min_length=1, max_length=500)
    lines: list[JournalLineInput] = Field(min_length=2)
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    exchange_rate: Decimal = Field(default=Decimal("1"), gt=0)
    reference: str | None = Field(default=None, max_length=100)
    source_module: str | None = Field(default=None, max_length=100)
    source_entity: str | None = Field(default=None, max_length=100)
    source_id: int | None = Field(default=None, gt=0)


class JournalEntryLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    line_number: int
    account_combination_id: int
    department_id: int | None
    cost_center_id: int | None
    description: str | None
    reference: str | None
    debit: Decimal
    credit: Decimal
    base_debit: Decimal
    base_credit: Decimal


class JournalEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    company_id: int
    branch_id: int
    journal_id: int
    fiscal_year_id: int
    period_id: int
    entry_number: str
    entry_date: date
    posting_date: date | None
    reference: str | None
    description: str
    currency_code: str
    exchange_rate: Decimal
    total_debit: Decimal
    total_credit: Decimal
    status: str
    source_module: str | None
    source_entity: str | None
    source_id: int | None
    lines: list[JournalEntryLineResponse] = Field(default_factory=list)


class JournalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    code: str
    name_ar: str
    name_en: str
    journal_type: str
    allow_manual_entries: bool
    auto_post: bool
    requires_approval: bool
    is_active: bool
