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
    def calculate(cls, amount, rate) -> TaxResult:
        base = cls._decimal(amount)
        percentage = cls._decimal(rate)
        if base < 0:
            raise TaxValidationError("Taxable amount cannot be negative")
        if percentage < 0 or percentage > 100:
            raise TaxValidationError("Tax rate must be between 0 and 100")
        tax = (base * percentage / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return TaxResult(base, tax, base + tax)

    @classmethod
    def reverse_tax(cls, total, rate) -> TaxResult:
        gross = cls._decimal(total)
        percentage = cls._decimal(rate)
        if gross < 0:
            raise TaxValidationError("Gross amount cannot be negative")
        if percentage < 0 or percentage >= 100:
            raise TaxValidationError("Reverse-tax rate must be between 0 and 100")
        base = (gross / (Decimal("1") + percentage / Decimal("100"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return TaxResult(base, gross - base, gross)

    @classmethod
    def calculate_multi(cls, amount, taxes: Iterable[TaxLine | tuple[str, Decimal | int | float | str]]) -> MultiTaxResult:
        base = cls._decimal(amount)
        if base < 0:
            raise TaxValidationError("Taxable amount cannot be negative")
        lines: list[TaxResult] = []
        seen: set[str] = set()
        for item in taxes:
            code, rate = (item.code, item.rate) if isinstance(item, TaxLine) else item
            code = str(code).strip().lower()
            if not code:
                raise TaxValidationError("Tax code is required")
            if code in seen:
                raise TaxValidationError(f"Duplicate tax code: {code}")
            seen.add(code)
            lines.append(cls.calculate(base, rate))
        total_tax = sum((line.tax_amount for line in lines), Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return MultiTaxResult(base, tuple(lines), total_tax, base + total_tax)

    @classmethod
    def calculate_inclusive(cls, gross_amount, taxes: Iterable[TaxLine | tuple[str, Decimal | int | float | str]]) -> MultiTaxResult:
        gross = cls._decimal(gross_amount)
        if gross < 0:
            raise TaxValidationError("Gross amount cannot be negative")
        normalized = list(taxes)
        total_rate = Decimal("0")
        seen: set[str] = set()
        for item in normalized:
            code, rate = (item.code, item.rate) if isinstance(item, TaxLine) else item
            code = str(code).strip().lower()
            if not code or code in seen:
                raise TaxValidationError("Tax code is required and must be unique")
            seen.add(code)
            percentage = cls._decimal(rate)
            if percentage < 0 or percentage > 100:
                raise TaxValidationError("Tax rate must be between 0 and 100")
            total_rate += percentage
        if total_rate == 0:
            return cls.calculate_multi(gross, normalized)
        base = (gross / (Decimal("1") + total_rate / Decimal("100"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        result = cls.calculate_multi(base, normalized)
        return MultiTaxResult(base, result.tax_lines, gross - base, gross)

    @classmethod
    def calculate_withholding(cls, amount, rate) -> TaxResult:
        """Calculate WHT as a deduction from payable, not an addition to gross."""
        base = cls._decimal(amount)
        percentage = cls._decimal(rate)
        if base < 0:
            raise TaxValidationError("Withholding base cannot be negative")
        if percentage < 0 or percentage > 100:
            raise TaxValidationError("Withholding rate must be between 0 and 100")
        withheld = (base * percentage / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return TaxResult(base, withheld, base - withheld)


tax_service = TaxService()
