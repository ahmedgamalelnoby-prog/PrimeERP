from datetime import date
from types import SimpleNamespace

import pytest

from app.modules.jurisdiction.tax_posting_guard import validate_snapshot_tax, validate_payment_wht


def snapshot(*rules, company_id=1):
    return SimpleNamespace(
        company_id=company_id,
        document_id=10,
        transaction_date=date(2026, 9, 14),
        rules=list(rules),
    )


def rule(code="VAT-14", tax_type="vat", rate="14"):
    return {"code": code, "tax_type": tax_type, "rate": rate}


def document(tax_total="14.00"):
    line = SimpleNamespace(line_total="100.00", quantity="1", unit_price="100", discount_percent="0")
    return SimpleNamespace(company_id=1, id=10, document_date=date(2026, 9, 14), tax_total=tax_total, lines=[line])


def test_snapshot_tax_accepts_matching_vat():
    validate_snapshot_tax(document("14.00"), snapshot(rule()))


def test_snapshot_tax_rejects_mismatch():
    with pytest.raises(Exception, match="does not match"):
        validate_snapshot_tax(document("15.00"), snapshot(rule()))


def test_snapshot_tax_rejects_tax_without_rule():
    with pytest.raises(Exception, match="no applicable"):
        validate_snapshot_tax(document("14.00"), snapshot())


def test_snapshot_tax_allows_zero_tax_when_no_rule():
    validate_snapshot_tax(document("0"), snapshot())


def test_snapshot_tax_rejects_cross_company_snapshot():
    with pytest.raises(Exception, match="does not belong"):
        validate_snapshot_tax(document("14.00"), snapshot(rule(), company_id=2))


def test_wht_matches_snapshot_rate():
    payment = SimpleNamespace(company_id=1, amount="1000", wht_amount="10")
    snap = SimpleNamespace(company_id=1, rules=[rule("WHT-1", "wht", "1")])
    validate_payment_wht(payment, snap)


def test_wht_rejects_mismatch():
    payment = SimpleNamespace(company_id=1, amount="1000", wht_amount="20")
    snap = SimpleNamespace(company_id=1, rules=[rule("WHT-1", "wht", "1")])
    with pytest.raises(Exception, match="does not match"):
        validate_payment_wht(payment, snap)


def test_wht_cannot_exceed_gross():
    payment = SimpleNamespace(company_id=1, amount="1000", wht_amount="1001")
    snap = SimpleNamespace(company_id=1, rules=[])
    with pytest.raises(Exception, match="between zero"):
        validate_payment_wht(payment, snap)
