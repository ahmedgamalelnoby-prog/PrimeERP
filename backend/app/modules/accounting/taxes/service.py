from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable


class TaxValidationError(ValueError):
    """Raised when tax input is invalid."""


@dataclass(frozen=True)
class TaxResult:
    taxable_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal


@dataclass(frozen=True)
class TaxLine:
    """A configurable tax component applied to the same taxable base."""

    code: str
    rate: Decimal


@dataclass(frozen=True)
class MultiTaxResult:
    taxable_amount: Decimal
    tax_lines: tuple[TaxResult, ...]
    tax_amount: Decimal
    total_amount: Decimal


class TaxService:
    """Pure tax calculation boundary used by sales, purchases and accounting."""

    @staticmethod
    def _decimal(value: Decimal | int | float | str) -> Decimal:
        try:
            return Decimal(str(value))
        except Exception as exc:
            raise TaxValidationError("Tax amount/rate must be numeric") from exc

    @classmethod
    def calculate(cls, amount: Decimal | int | float | str, rate: Decimal | int | float | str) -> TaxResult:
        base = cls._decimal(amount)
        percentage = cls._decimal(rate)
        if base < 0:
            raise TaxValidationError("Taxable amount cannot be negative")
        if percentage < 0 or percentage > 100:
            raise TaxValidationError("Tax rate must be between 0 and 100")
        tax = (base * percentage / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return TaxResult(base, tax, base + tax)

    @classmethod
    def reverse_tax(cls, total: Decimal | int | float | str, rate: Decimal | int | float | str) -> TaxResult:
        gross = cls._decimal(total)
        percentage = cls._decimal(rate)
        if gross < 0:
            raise TaxValidationError("Gross amount cannot be negative")
        if percentage < 0 or percentage >= 100:
            raise TaxValidationError("Reverse-tax rate must be between 0 and 100")
        base = (gross / (Decimal("1") + percentage / Decimal("100"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        tax = gross - base
        return TaxResult(base, tax, gross)

    @classmethod
    def calculate_multi(
        cls,
        amount: Decimal | int | float | str,
        taxes: Iterable[TaxLine | tuple[str, Decimal | int | float | str]],
    ) -> MultiTaxResult:
        """Calculate multiple additive taxes (VAT + other taxes) on one base.

        Each tax is calculated from the original taxable amount, avoiding accidental
        compounding. Withholding taxes remain a separate payable-side calculation.
        """
        base = cls._decimal(amount)
        if base < 0:
            raise TaxValidationError("Taxable amount cannot be negative")

        lines: list[TaxResult] = []
        seen: set[str] = set()
        for item in taxes:
            if isinstance(item, TaxLine):
                code, rate = item.code, item.rate
            else:
                code, rate = item
            code = str(code).strip().lower()
            if not code:
                raise TaxValidationError("Tax code is required")
            if code in seen:
                raise TaxValidationError(f"Duplicate tax code: {code}")
            seen.add(code)
            lines.append(cls.calculate(base, rate))

        total_tax = sum((line.tax_amount for line in lines), Decimal("0.00")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return MultiTaxResult(
            taxable_amount=base,
            tax_lines=tuple(lines),
            tax_amount=total_tax,
            total_amount=base + total_tax,
        )


tax_service = TaxService()
