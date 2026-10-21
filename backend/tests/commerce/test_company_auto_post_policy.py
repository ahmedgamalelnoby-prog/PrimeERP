from datetime import date
from types import SimpleNamespace

import pytest

import app.modules.commerce.accounting_service as accounting_module


class FakeDB:
    def __init__(self, journal):
        self.journal = journal
        self.scalar_calls = 0

    def scalar(self, _query):
        self.scalar_calls += 1
        # First query checks for an existing source journal; second loads the journal.
        return None if self.scalar_calls == 1 else self.journal


def _run_post(monkeypatch, company_auto_post_enabled, *, policy_key="accounting.auto_post_sales_invoice", source_entity="sales_invoice"):
    journal = SimpleNamespace(id=11, requires_approval=False, auto_post=True)
    db = FakeDB(journal)
    service = accounting_module.CommerceAccountingService()
    settings = SimpleNamespace(default_branch_id=3, auto_post=True)
    monkeypatch.setattr(service, "_context", lambda *_args: (settings, 5, SimpleNamespace(id=6), SimpleNamespace(id=8)))
    monkeypatch.setattr(accounting_module, "validate_double_entry", lambda _lines: None)
    monkeypatch.setattr(accounting_module, "validate_source", lambda **_kwargs: None)
    monkeypatch.setattr(
        accounting_module,
        "get_company_setting",
        lambda _db, _company_id, key: company_auto_post_enabled if key == policy_key else None,
    )
    calls = []
    monkeypatch.setattr(accounting_module.journal_service, "create_draft", lambda *_args, **_kwargs: SimpleNamespace(id=99))
    monkeypatch.setattr(accounting_module.journal_service, "submit", lambda *_args, **_kwargs: calls.append("submit"))
    monkeypatch.setattr(accounting_module.journal_service, "approve", lambda *_args, **_kwargs: calls.append("approve"))
    monkeypatch.setattr(accounting_module.journal_service, "post", lambda *_args, **_kwargs: calls.append("post"))
    result = service._post(
        db,
        company_id=7,
        user_id=42,
        entry_date=date(2026, 10, 20),
        journal_id=11,
        entry_number="SI-100",
        description="Sales invoice 100",
        lines=[{"debit": 10, "credit": 0}, {"debit": 0, "credit": 10}],
        source_entity=source_entity,
        source_id=100,
        auto_post_policy_key=policy_key,
    )
    return result, calls


def test_company_policy_disables_automatic_sales_invoice_journal_posting(monkeypatch):
    result, calls = _run_post(monkeypatch, False)

    assert result.id == 99
    assert calls == ["submit"]


def test_company_policy_allows_automatic_sales_invoice_journal_posting(monkeypatch):
    result, calls = _run_post(monkeypatch, True)

    assert result.id == 99
    assert calls == ["submit", "post"]


def test_company_policy_disables_automatic_purchase_bill_journal_posting(monkeypatch):
    result, calls = _run_post(
        monkeypatch,
        False,
        policy_key="accounting.auto_post_purchase_invoice",
        source_entity="purchase_bill",
    )

    assert result.id == 99
    assert calls == ["submit"]


def test_company_policy_allows_automatic_purchase_bill_journal_posting(monkeypatch):
    result, calls = _run_post(
        monkeypatch,
        True,
        policy_key="accounting.auto_post_purchase_invoice",
        source_entity="purchase_bill",
    )

    assert result.id == 99
    assert calls == ["submit", "post"]



def test_company_account_code_default_overrides_legacy_account_id(monkeypatch):
    db = SimpleNamespace(scalar=lambda _query: 812)
    monkeypatch.setattr(
        accounting_module,
        "get_company_setting",
        lambda _db, _company_id, key: "01005101" if key == "accounting.default_receivable_account" else "",
    )

    service = accounting_module.CommerceAccountingService()
    assert service._configured_account_id(
        db, 7, "accounting.default_receivable_account", 123
    ) == 812


def test_company_account_code_default_uses_legacy_fallback_when_unset(monkeypatch):
    db = SimpleNamespace(scalar=lambda _query: pytest.fail("account lookup must not run"))
    monkeypatch.setattr(accounting_module, "get_company_setting", lambda *_args: "")

    service = accounting_module.CommerceAccountingService()
    assert service._configured_account_id(
        db, 7, "accounting.default_receivable_account", 123
    ) == 123


def test_company_account_code_default_rejects_unknown_account(monkeypatch):
    from fastapi import HTTPException
    import pytest

    db = SimpleNamespace(scalar=lambda _query: None)
    monkeypatch.setattr(accounting_module, "get_company_setting", lambda *_args: "99999999")

    service = accounting_module.CommerceAccountingService()
    with pytest.raises(HTTPException) as exc:
        service._configured_account_id(
            db, 7, "accounting.default_receivable_account", 123
        )
    assert exc.value.status_code == 409

@pytest.mark.parametrize(
    ("invoice_value", "receipt_value", "tolerance", "allow_beyond", "should_raise"),
    [
        ("100", "100", 0, False, False),
        ("101", "100", 1, False, False),
        ("102", "100", 1, False, True),
        ("102", "100", 1, True, False),
        ("90", "100", 10, False, False),
    ],
)
def test_company_purchase_price_variance_tolerance(
    monkeypatch, invoice_value, receipt_value, tolerance, allow_beyond, should_raise
):
    from decimal import Decimal
    from fastapi import HTTPException

    values = {
        "purchasing.price_variance_tolerance_pct": tolerance,
        "purchasing.allow_invoice_price_variance": allow_beyond,
    }
    monkeypatch.setattr(
        accounting_module,
        "get_company_setting",
        lambda _db, _company_id, key: values[key],
    )
    service = accounting_module.CommerceAccountingService()
    check = lambda: service._validate_purchase_price_variance(
        SimpleNamespace(),
        company_id=7,
        invoice_value=Decimal(invoice_value),
        receipt_value=Decimal(receipt_value),
    )
    if should_raise:
        with pytest.raises(HTTPException) as exc:
            check()
        assert exc.value.status_code == 409
    else:
        check()

def test_company_account_code_overrides_do_not_mutate_persisted_legacy_settings(monkeypatch):
    from app.modules.commerce.accounting_models import CommerceAccountingSettings

    legacy = CommerceAccountingSettings(
        company_id=7,
        sales_journal_id=1,
        purchase_journal_id=2,
        cash_journal_id=3,
        ar_account_id=101,
        ap_account_id=102,
        sales_account_id=103,
        purchase_account_id=104,
        inventory_account_id=105,
        grni_account_id=106,
        cogs_account_id=107,
        output_vat_account_id=108,
        input_vat_account_id=109,
        default_payment_account_id=110,
        default_branch_id=4,
        auto_post=True,
    )
    resolved = iter([201, 202, 203, 204, 205])

    class SettingsDB:
        def scalar(self, _query):
            # The first lookup loads the persisted settings; subsequent lookups
            # resolve configured account codes without writing to the ORM object.
            if not hasattr(self, "loaded"):
                self.loaded = True
                return legacy
            return next(resolved)

    db = SettingsDB()
    monkeypatch.setattr(
        accounting_module,
        "get_company_setting",
        lambda _db, _company_id, key: {
            "accounting.default_receivable_account": "AR",
            "accounting.default_payable_account": "AP",
            "accounting.default_sales_account": "SALES",
            "accounting.default_purchase_account": "PURCHASE",
            "accounting.default_cash_account": "CASH",
        }[key],
    )

    effective = accounting_module.CommerceAccountingService()._settings(db, 7)

    assert (
        effective.ar_account_id,
        effective.ap_account_id,
        effective.sales_account_id,
        effective.purchase_account_id,
        effective.default_payment_account_id,
    ) == (201, 202, 203, 204, 205)
    assert (
        legacy.ar_account_id,
        legacy.ap_account_id,
        legacy.sales_account_id,
        legacy.purchase_account_id,
        legacy.default_payment_account_id,
    ) == (101, 102, 103, 104, 110)
