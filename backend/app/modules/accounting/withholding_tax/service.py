from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


class WithholdingTaxValidationError(ValueError):
    """Raised when withholding-tax input is invalid."""


@dataclass(frozen=True)
class WithholdingResult:
    gross_amount: Decimal
    withheld_amount: Decimal
    net_amount: Decimal


class WithholdingTaxService:
    @staticmethod
    def calculate(gross_amount: Decimal | int | float | str, rate: Decimal | int | float | str) -> WithholdingResult:
        gross = Decimal(str(gross_amount))
        percentage = Decimal(str(rate))
        if gross < 0:
            raise WithholdingTaxValidationError("Gross amount cannot be negative")
        if percentage < 0 or percentage > 100:
            raise WithholdingTaxValidationError("Withholding rate must be between 0 and 100")
        withheld = (gross * percentage / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return WithholdingResult(gross, withheld, gross - withheld)


withholding_tax_service = WithholdingTaxService()
