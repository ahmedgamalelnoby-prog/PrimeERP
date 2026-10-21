from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

MovementType = Literal["receipt", "issue", "transfer", "adjustment", "opening", "return", "production_issue", "production_receipt"]


class StockMoveCreate(BaseModel):
    company_id: int = Field(gt=0)
    item_id: int = Field(gt=0)
    variant_id: int | None = Field(default=None, gt=0)
    source_location_id: int | None = Field(default=None, gt=0)
    destination_location_id: int | None = Field(default=None, gt=0)
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)
    movement_type: MovementType
    transaction_date: date | None = None
    reference: str | None = Field(default=None, max_length=100)
    source_module: str | None = Field(default=None, max_length=80)
    source_entity: str | None = Field(default=None, max_length=80)
    source_id: str | None = Field(default=None, max_length=80)
    reservation_id: int | None = Field(default=None, gt=0)
    notes: str | None = None


class StockMoveResponse(StockMoveCreate):
    id: int
    status: str
    posted_at: object | None = None
    accounting_entry_id: int | None = None

    class Config:
        from_attributes = True


class InventoryAccountingConfigCreate(BaseModel):
    company_id: int = Field(gt=0)
    journal_id: int = Field(gt=0)
    branch_id: int = Field(gt=0)
    inventory_account_id: int = Field(gt=0)
    cogs_account_id: int = Field(gt=0)
    adjustment_account_id: int = Field(gt=0)
    clearing_account_id: int = Field(gt=0)


class InventoryAccountingConfigResponse(InventoryAccountingConfigCreate):
    id: int
    tenant_id: int
    is_active: str

    class Config:
        from_attributes = True
