from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class ReceivableStatus(StrEnum):
    OPEN = "open"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Receivable:
    document_id: str
    customer_id: str
    gross_amount: Decimal
    paid_amount: Decimal = Decimal("0")

    @property
    def balance(self) -> Decimal:
        return self.gross_amount - self.paid_amount

    @property
    def status(self) -> ReceivableStatus:
        if self.balance <= 0:
            return ReceivableStatus.PAID
        if self.paid_amount > 0:
            return ReceivableStatus.PARTIALLY_PAID
        return ReceivableStatus.OPEN


class ReceivableService:
    @staticmethod
    def apply_payment(receivable: Receivable, amount: Decimal | int | float | str) -> Receivable:
        payment = Decimal(str(amount))
        if payment <= 0:
            raise ValueError("Payment amount must be positive")
        if payment > receivable.balance:
            raise ValueError("Payment cannot exceed receivable balance")
        return Receivable(receivable.document_id, receivable.customer_id, receivable.gross_amount, receivable.paid_amount + payment)


receivable_service = ReceivableService()
