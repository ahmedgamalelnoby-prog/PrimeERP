from datetime import date, datetime
from typing import Any, Literal, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


TransactionStatus = Literal[
    "draft",
    "pending",
    "approved",
    "posted",
    "cancelled",
    "reversed",
]

TransactionType = Literal[
    "sales_invoice",
    "purchase_invoice",
    "receipt",
    "payment",
    "journal_entry",
    "stock_receipt",
    "stock_issue",
    "stock_transfer",
    "sales_return",
    "purchase_return",
    "reservation",
    "shipment",
    "payroll",
    "manufacturing",
    "general",
]


class TransactionCreate(BaseModel):
    company_id: int = Field(
        gt=0,
    )

    project_id: Optional[int] = Field(default=None, gt=0)

    branch_id: int = Field(
        gt=0,
    )

    transaction_type: TransactionType

    source_module: str = Field(
        min_length=2,
        max_length=80,
    )

    source_entity: str = Field(
        min_length=2,
        max_length=100,
    )

    source_id: Optional[int] = Field(
        default=None,
        gt=0,
    )

    document_number: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    reference_number: Optional[str] = Field(
        default=None,
        max_length=150,
    )

    external_reference: Optional[str] = Field(
        default=None,
        max_length=150,
    )

    transaction_date: date = Field(
        default_factory=date.today,
    )

    metadata_json: Optional[
        dict[str, Any]
    ] = None

    @field_validator(
        "source_module",
        "source_entity",
    )
    @classmethod
    def normalize_identifier(
        cls,
        value: str,
    ) -> str:
        return (
            value
            .strip()
            .lower()
            .replace(" ", "_")
        )


class TransactionUpdate(BaseModel):
    project_id: Optional[int] = Field(default=None, gt=0)

    document_number: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    reference_number: Optional[str] = Field(
        default=None,
        max_length=150,
    )

    external_reference: Optional[str] = Field(
        default=None,
        max_length=150,
    )

    transaction_date: Optional[date] = None

    metadata_json: Optional[
        dict[str, Any]
    ] = None


class TransactionActionRequest(BaseModel):
    reason: Optional[str] = Field(
        default=None,
        max_length=1000,
    )


class TransactionCancelRequest(BaseModel):
    reason: str = Field(
        min_length=3,
        max_length=1000,
    )


class TransactionReverseRequest(BaseModel):
    reason: str = Field(
        min_length=3,
        max_length=1000,
    )


class TransactionEventResponse(BaseModel):
    id: int

    event_type: str

    previous_status: Optional[str]

    new_status: Optional[str]

    description: Optional[str]

    event_data: Optional[
        dict[str, Any]
    ]

    performed_by: Optional[int]

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class TransactionResponse(BaseModel):
    id: int

    tenant_id: int

    company_id: int

    project_id: Optional[int]

    branch_id: int

    transaction_number: str

    transaction_type: str

    document_number: Optional[str]

    status: str

    source_module: str

    source_entity: str

    source_id: Optional[int]

    reference_number: Optional[str]

    external_reference: Optional[str]

    transaction_date: date

    posting_date: Optional[date]

    original_transaction_id: Optional[int]

    reversal_transaction_id: Optional[int]

    cancellation_reason: Optional[str]

    metadata_json: Optional[
        dict[str, Any]
    ]

    is_cancelled: bool

    is_reversed: bool

    created_by: Optional[int]

    approved_by: Optional[int]

    posted_by: Optional[int]

    cancelled_by: Optional[int]

    created_at: datetime

    approved_at: Optional[datetime]

    posted_at: Optional[datetime]

    cancelled_at: Optional[datetime]

    updated_at: datetime

    events: list[
        TransactionEventResponse
    ] = []

    model_config = ConfigDict(
        from_attributes=True
    )


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]

    total: int

    page: int

    page_size: int

    pages: int