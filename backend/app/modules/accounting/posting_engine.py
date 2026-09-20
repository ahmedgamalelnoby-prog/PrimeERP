"""Deterministic double-entry posting invariants for PrimeERP.

This layer is persistence-agnostic. Database services remain responsible for
scope, periods, permissions and persistence; this module guarantees that the
financial payload itself is valid and that reversals are exact opposites.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


class PostingValidationError(ValueError):
    """Raised when a journal payload violates double-entry invariants."""


ZERO = Decimal("0")


@dataclass(frozen=True)
class PostingLine:
    account_combination_id: int
    debit: Decimal = ZERO
    credit: Decimal = ZERO
    department_id: int | None = None
    cost_center_id: int | None = None


def normalize_amount(value: object) -> Decimal:
    try:
        amount = Decimal(str(value))
    except Exception as exc:
        raise PostingValidationError("Amount must be a valid decimal") from exc
    if not amount.is_finite() or amount < ZERO:
        raise PostingValidationError("Amounts must be finite and non-negative")
    return amount


def validate_line(line: PostingLine, line_number: int) -> None:
    debit = normalize_amount(line.debit)
    credit = normalize_amount(line.credit)
    if line.account_combination_id <= 0:
        raise PostingValidationError(f"Invalid account on journal line {line_number}")
    if debit > ZERO and credit > ZERO:
        raise PostingValidationError(
            f"Journal line {line_number} cannot contain both debit and credit"
        )
    if debit == ZERO and credit == ZERO:
        raise PostingValidationError(
            f"Journal line {line_number} must contain a debit or credit amount"
        )


def validate_balanced(lines: list[PostingLine]) -> tuple[Decimal, Decimal]:
    if len(lines) < 2:
        raise PostingValidationError("Journal entry requires at least two lines")
    for number, line in enumerate(lines, start=1):
        validate_line(line, number)
    debit = sum((normalize_amount(line.debit) for line in lines), ZERO)
    credit = sum((normalize_amount(line.credit) for line in lines), ZERO)
    if debit != credit:
        raise PostingValidationError(
            f"Journal entry must be balanced: debit={debit} credit={credit}"
        )
    if debit <= ZERO:
        raise PostingValidationError("Journal entry total must be greater than zero")
    return debit, credit


def reversal_lines(lines: list[PostingLine]) -> list[PostingLine]:
    """Return an exact debit/credit inversion without mutating the source."""
    validate_balanced(lines)
    return [
        PostingLine(
            account_combination_id=line.account_combination_id,
            debit=normalize_amount(line.credit),
            credit=normalize_amount(line.debit),
            department_id=line.department_id,
            cost_center_id=line.cost_center_id,
        )
        for line in lines
    ]
