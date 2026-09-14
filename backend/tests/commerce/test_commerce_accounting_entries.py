from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.modules.commerce.accounting_service import CommerceAccountingService


class _Settings:
    ar_account_id = 101
    ap_account_id = 102
    sales_account_id = 103
    purchase_account_id = 104
    inventory_account_id = 105
    cogs_account_id = 106
    output_vat_account_id = 107
    input_vat_account_id = 108
    wht_account_id = 109
    default_payment_account_id = 110
    sales_journal_id = 201
    purchase_journal_id = 202
    cash_journal_id = 203
    default_branch_id = 301
    auto_post = True


def _capture(method_name, document, monkeypatch):
    service = CommerceAccountingService()
    captured = {}

    monkeypatch.setattr(service, "_settings", lambda db, company_id: _Settings())

    def fake_post(db, **kwargs):
        captured.update(kwargs)
        return kwargs

    monkeypatch.setattr(service, "_post", fake_post)
    getattr(service, method_name)(object(), document, 77)
    return captured["lines"]


def _assert_balanced(lines):
    assert sum(Decimal(str(x["debit"])) for x in lines) == sum(Decimal(str(x["credit"])) for x in lines)


def test_sales_invoice_posts_ar_revenue_and_output_vat(monkeypatch):
    document = SimpleNamespace(company_id=1, id=10, number="SI-10", document_date=date(2026, 9, 14), subtotal=Decimal("100"), tax_total=Decimal("14"), total=Decimal("114"))
    lines = _capture("post_sales_invoice", document, monkeypatch)

    assert [(x["account_combination_id"], x["debit"], x["credit"]) for x in lines] == [
        (101, Decimal("114"), 0),
        (103, 0, Decimal("100")),
        (107, 0, Decimal("14")),
    ]
    _assert_balanced(lines)


def test_sales_credit_note_is_exact_accounting_direction_reversal(monkeypatch):
    document = SimpleNamespace(company_id=1, id=11, number="SCN-11", document_date=date(2026, 9, 14), subtotal=Decimal("100"), tax_total=Decimal("14"), total=Decimal("114"))
    lines = _capture("post_sales_credit_note", document, monkeypatch)

    assert [(x["account_combination_id"], x["debit"], x["credit"]) for x in lines] == [
        (103, Decimal("100"), 0),
        (107, Decimal("14"), 0),
        (101, 0, Decimal("114")),
    ]
    _assert_balanced(lines)


def test_payment_wht_is_separated_from_cash_for_customer_receipt(monkeypatch):
    payment = SimpleNamespace(company_id=1, id=12, document_kind="sale", amount=Decimal("114"), wht_amount=Decimal("4"), payment_date=date(2026, 9, 14))
    document = SimpleNamespace()
    service = CommerceAccountingService()
    captured = {}
    monkeypatch.setattr(service, "_settings", lambda db, company_id: _Settings())
    monkeypatch.setattr(service, "_post", lambda db, **kwargs: captured.update(kwargs) or kwargs)

    service.post_payment(object(), payment, document, 77)
    lines = captured["lines"]

    assert [(x["account_combination_id"], x["debit"], x["credit"]) for x in lines] == [
        (110, Decimal("110"), 0),
        (109, Decimal("4"), 0),
        (101, 0, Decimal("114")),
    ]
    _assert_balanced(lines)


def test_payment_wht_is_separated_from_cash_for_vendor_payment(monkeypatch):
    payment = SimpleNamespace(company_id=1, id=13, document_kind="purchase", amount=Decimal("114"), wht_amount=Decimal("4"), payment_date=date(2026, 9, 14))
    document = SimpleNamespace()
    service = CommerceAccountingService()
    captured = {}
    monkeypatch.setattr(service, "_settings", lambda db, company_id: _Settings())
    monkeypatch.setattr(service, "_post", lambda db, **kwargs: captured.update(kwargs) or kwargs)

    service.post_payment(object(), payment, document, 77)
    lines = captured["lines"]

    assert [(x["account_combination_id"], x["debit"], x["credit"]) for x in lines] == [
        (102, Decimal("114"), 0),
        (110, 0, Decimal("110")),
        (109, 0, Decimal("4")),
    ]
    _assert_balanced(lines)
