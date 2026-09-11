from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


class TaxValidationError(ValueError):
    """Raised when tax input is invalid."""


@dataclass(frozen=True)
class TaxResult:
    taxable_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal


class TaxService:
    """Pure tax calculation boundary used by sales, purchases and accounting."""

    @staticmethod
    def calculate(amount: Decimal | int | float | str, rate: Decimal | int | float | str) -> TaxResult:
        base = Decimal(str(amount))
        percentage = Decimal(str(rate))
        if base < 0:
            raise TaxValidationError("Taxable amount cannot be negative")
        if percentage < 0 or percentage > 100:
            raise TaxValidationError("Tax rate must be between 0 and 100")
        tax = (base * percentage / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return TaxResult(base, tax, base + tax)

    @staticmethod
    def reverse_tax(total: Decimal | int | float | str, rate: Decimal | int | float | str) -> TaxResult:
        gross = Decimal(str(total))
        percentage = Decimal(str(rate))
        if gross < 0:
            raise TaxValidationError("Gross amount cannot be negative")
        if percentage < 0 or percentage >= 100:
            raise TaxValidationError("Reverse-tax rate must be between 0 and 100")
        base = (gross / (Decimal("1") + percentage / Decimal("100"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        tax = gross - base
        return TaxResult(base, tax, gross)


tax_service = TaxService()
