import pytest
from datetime import date

from app.modules.commerce.service import resolve_due_date


def test_invoice_due_date_uses_partner_terms_when_not_explicit():
    assert resolve_due_date("invoice", date(2026, 9, 1), None, 30) == date(2026, 10, 1)


def test_bill_explicit_due_date_is_preserved():
    assert resolve_due_date("bill", date(2026, 9, 1), date(2026, 9, 20), 30) == date(2026, 9, 20)


def test_non_financial_document_has_no_due_date():
    assert resolve_due_date("order", date(2026, 9, 1), None, 30) is None


def test_due_date_cannot_precede_document_date():
    with pytest.raises(ValueError, match="earlier"):
        resolve_due_date("invoice", date(2026, 9, 10), date(2026, 9, 9), 30)
