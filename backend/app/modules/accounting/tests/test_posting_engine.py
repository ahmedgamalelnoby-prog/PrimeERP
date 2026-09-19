from decimal import Decimal

import pytest

from app.modules.accounting.posting_engine import (
    PostingLine,
    PostingValidationError,
    reversal_lines,
    validate_balanced,
)


def test_balanced_double_entry_is_accepted():
    debit, credit = validate_balanced([
        PostingLine(101, debit=Decimal("100")),
        PostingLine(202, credit=Decimal("100")),
    ])
    assert debit == Decimal("100")
    assert credit == Decimal("100")


def test_unbalanced_entry_is_rejected():
    with pytest.raises(PostingValidationError, match="balanced"):
        validate_balanced([
            PostingLine(101, debit=Decimal("100")),
            PostingLine(202, credit=Decimal("99.99")),
        ])


def test_line_cannot_have_both_sides():
    with pytest.raises(PostingValidationError, match="both debit and credit"):
        validate_balanced([
            PostingLine(101, debit=Decimal("100"), credit=Decimal("1")),
            PostingLine(202, credit=Decimal("101")),
        ])


def test_zero_lines_are_rejected():
    with pytest.raises(PostingValidationError, match="must contain"):
        validate_balanced([
            PostingLine(101),
            PostingLine(202, credit=Decimal("1")),
        ])


def test_reversal_is_exact_opposite():
    original = [
        PostingLine(101, debit=Decimal("125.50")),
        PostingLine(202, credit=Decimal("125.50")),
    ]
    reversed_payload = reversal_lines(original)
    assert reversed_payload[0].debit == Decimal("0")
    assert reversed_payload[0].credit == Decimal("125.50")
    assert reversed_payload[1].debit == Decimal("125.50")
    assert reversed_payload[1].credit == Decimal("0")
    validate_balanced(reversed_payload)
