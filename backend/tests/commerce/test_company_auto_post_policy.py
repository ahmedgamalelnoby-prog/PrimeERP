from datetime import date
from types import SimpleNamespace

import app.modules.commerce.accounting_service as accounting_module


class FakeDB:
    def __init__(self, journal):
        self.journal = journal
        self.scalar_calls = 0

    def scalar(self, _query):
        self.scalar_calls += 1
        # First query checks for an existing source journal; second loads the journal.
        return None if self.scalar_calls == 1 else self.journal


def _run_post(monkeypatch, company_auto_post_enabled):
    journal = SimpleNamespace(id=11, requires_approval=False, auto_post=True)
    db = FakeDB(journal)
    service = accounting_module.CommerceAccountingService()
    settings = SimpleNamespace(default_branch_id=3, auto_post=True)
    monkeypatch.setattr(service, "_context", lambda *_args: (settings, 5, object(), SimpleNamespace(id=8)))
    monkeypatch.setattr(accounting_module, "validate_double_entry", lambda _lines: None)
    monkeypatch.setattr(accounting_module, "validate_source", lambda **_kwargs: None)
    monkeypatch.setattr(
        accounting_module,
        "get_company_setting",
        lambda _db, _company_id, key: company_auto_post_enabled if key == "accounting.auto_post_sales_invoice" else None,
    )
    calls = []
    monkeypatch.setattr(accounting_module.journal_service, "create_draft", lambda **_kwargs: SimpleNamespace(id=99))
    monkeypatch.setattr(accounting_module.journal_service, "submit", lambda **_kwargs: calls.append("submit"))
    monkeypatch.setattr(accounting_module.journal_service, "approve", lambda **_kwargs: calls.append("approve"))
    monkeypatch.setattr(accounting_module.journal_service, "post", lambda **_kwargs: calls.append("post"))
    result = service._post(
        db,
        company_id=7,
        user_id=42,
        entry_date=date(2026, 10, 20),
        journal_id=11,
        entry_number="SI-100",
        description="Sales invoice 100",
        lines=[{"debit": 10, "credit": 0}, {"debit": 0, "credit": 10}],
        source_entity="sales_invoice",
        source_id=100,
        auto_post_policy_key="accounting.auto_post_sales_invoice",
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
