"""Accounting impact contract used by operational modules.

Operational modules describe what happened; the accounting engine decides the
actual journal entry using company/branch/chart-of-accounts configuration.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping


@dataclass(frozen=True)
class AccountingImpact:
    source_module: str
    source_entity: str
    source_id: str
    event: str
    debit_account_role: str
    credit_account_role: str
    amount: Decimal
    currency: str = "EGP"
    metadata: Mapping[str, str] | None = None


@dataclass(frozen=True)
class FinancialImpact:
    """Single business event's normalized impact on the financial statements."""

    revenue: Decimal = Decimal("0")
    cogs: Decimal = Decimal("0")
    inventory: Decimal = Decimal("0")
    receivable: Decimal = Decimal("0")
    payable: Decimal = Decimal("0")
    cash: Decimal = Decimal("0")
    operating_expense: Decimal = Decimal("0")

    @property
    def gross_profit(self) -> Decimal:
        return self.revenue - self.cogs
