from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Payable:
    document_id: str
    supplier_id: str
    gross_amount: Decimal
    paid_amount: Decimal = Decimal("0")

    @property
    def balance(self) -> Decimal:
        return self.gross_amount - self.paid_amount


class PayableService:
    @staticmethod
    def apply_payment(payable: Payable, amount: Decimal | int | float | str) -> Payable:
        payment = Decimal(str(amount))
        if payment <= 0:
            raise ValueError("Payment amount must be positive")
        if payment > payable.balance:
            raise ValueError("Payment cannot exceed payable balance")
        return Payable(payable.document_id, payable.supplier_id, payable.gross_amount, payable.paid_amount + payment)


payable_service = PayableService()
