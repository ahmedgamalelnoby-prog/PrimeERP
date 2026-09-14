from datetime import date
from types import SimpleNamespace

import pytest

from app.modules.jurisdiction.tax_posting_guard import validate_snapshot_tax, validate_payment_wht


def snapshot(*rules, company_id=1, document_id=10, facts=None):
    return SimpleNamespace(
        company_id=company_id,
        document_id=document_id,
        transaction_date=date(2026, 9, 14),
        rules=list(rules),
        facts=facts or {"document_subtotal": "100.00", "document_total": "114.00"},
    )


def rule(code="VAT-14", tax_type="vat", rate="14"):
    return {"code": code, "tax_type": tax_type, "rate": rate}


def document(tax_total="14.00", subtotal="100.00", total="114.00", document_id=10):
    line = SimpleNamespace(line_total="114.00", quantity="1", unit_price="100", discount_percent="0")
    return SimpleNamespace(company_id=1, id=document_id, document_date=date(2026, 9, 14), subtotal=subtotal, total=total, tax_total=tax_total, lines=[line])


def test_snapshot_tax_uses_untaxed_subtotal_not_line_total():
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
    snap = snapshot(rule("WHT-1", "wht", "1"), facts={"document_subtotal": "1000", "document_total": "1000"})
    validate_payment_wht(payment, snap)


def test_wht_partial_payment_is_allocated_from_document_taxable_base():
    payment = SimpleNamespace(company_id=1, amount="500", wht_amount="5")
    snap = snapshot(rule("WHT-1", "wht", "1"), facts={"document_subtotal": "1000", "document_total": "1000"})
    validate_payment_wht(payment, snap)


def test_wht_rejects_mismatch():
    payment = SimpleNamespace(company_id=1, amount="1000", wht_amount="20")
    snap = snapshot(rule("WHT-1", "wht", "1"), facts={"document_subtotal": "1000", "document_total": "1000"})
    with pytest.raises(Exception, match="does not match"):
        validate_payment_wht(payment, snap)


def test_wht_rejects_when_snapshot_has_no_rule():
    payment = SimpleNamespace(company_id=1, amount="1000", wht_amount="1")
    snap = snapshot()
    with pytest.raises(Exception, match="no WHT rule"):
        validate_payment_wht(payment, snap)


def test_wht_cannot_exceed_gross():
    payment = SimpleNamespace(company_id=1, amount="1000", wht_amount="1001")
    snap = snapshot()
    with pytest.raises(Exception, match="between zero"):
        validate_payment_wht(payment, snap)
