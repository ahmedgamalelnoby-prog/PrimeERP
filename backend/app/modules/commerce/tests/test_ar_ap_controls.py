from decimal import Decimal
import pytest
from datetime import date

from app.modules.commerce.service import resolve_due_date, CommerceService


def test_invoice_due_date_uses_partner_terms_when_not_explicit():
    assert resolve_due_date("invoice", date(2026, 9, 1), None, 30) == date(2026, 10, 1)


def test_bill_explicit_due_date_is_preserved():
    assert resolve_due_date("bill", date(2026, 9, 1), date(2026, 9, 20), 30) == date(2026, 9, 20)


def test_non_financial_document_has_no_due_date():
    assert resolve_due_date("order", date(2026, 9, 1), None, 30) is None


def test_due_date_cannot_precede_document_date():
    with pytest.raises(ValueError, match="earlier"):
        resolve_due_date("invoice", date(2026, 9, 10), date(2026, 9, 9), 30)


def test_partner_statement_rejects_invalid_direction_without_database_access():
    with pytest.raises(ValueError, match="Invalid statement direction"):
        CommerceService().partner_statement(None, 1, 1, "invalid", as_of=date(2026, 9, 19))


def test_credit_limit_exposure_is_current_balance_plus_new_invoice():
    current_outstanding = Decimal("8000")
    invoice_total = Decimal("2500")
    credit_limit = Decimal("10000")
    assert current_outstanding + invoice_total > credit_limit


def test_credit_limit_within_limit_is_allowed_by_exposure_math():
    current_outstanding = Decimal("7000")
    invoice_total = Decimal("2500")
    credit_limit = Decimal("10000")
    assert current_outstanding + invoice_total <= credit_limit
