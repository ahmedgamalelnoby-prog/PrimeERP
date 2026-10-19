from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import app.modules.accounting.journals.services.journal_service as service_module


class FakeDB:
    def __init__(self, lines):
        self.lines = lines
        self.flushed = False

    def scalars(self, _query):
        return SimpleNamespace(all=lambda: self.lines)

    def flush(self):
        self.flushed = True


def _entry():
    return SimpleNamespace(
        id=10,
        company_id=20,
        status="pending",
        journal=SimpleNamespace(requires_approval=False),
        period_id=30,
        fiscal_year_id=40,
        entry_date=date(2026, 10, 10),
        total_debit=Decimal("0"),
        total_credit=Decimal("0"),
        posting_date=None,
        posted_by=None,
        posted_at=None,
    )


def _period():
    return SimpleNamespace(
        company_id=20,
        fiscal_year_id=40,
        status="open",
        allow_posting=True,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 31),
    )


def _lines():
    return [
        SimpleNamespace(account_combination_id=1, debit=Decimal("100"), credit=Decimal("0"), department_id=None, cost_center_id=None),
        SimpleNamespace(account_combination_id=2, debit=Decimal("0"), credit=Decimal("100"), department_id=None, cost_center_id=None),
    ]


def _wire(monkeypatch, entry, db, policy):
    monkeypatch.setattr(service_module.journal_service, "_locked_entry", lambda *_args, **_kwargs: entry)
    monkeypatch.setattr(service_module, "get_company_setting", lambda _db, _company_id, _key: policy)
    monkeypatch.setattr(
        service_module.fiscal_year_repository,
        "get_period_by_id",
        lambda *_args, **_kwargs: _period(),
    )


def test_company_policy_blocks_pending_journal_without_approval(monkeypatch):
    entry = _entry()
    db = FakeDB(_lines())
    _wire(monkeypatch, entry, db, True)

    with pytest.raises(HTTPException) as exc:
        service_module.journal_service.post(db, tenant_id=1, entry_id=10, user_id=99, commit=False)

    assert exc.value.status_code == 409
    assert "approval is required" in exc.value.detail.lower()
    assert not db.flushed


def test_company_policy_can_allow_posting_when_journal_does_not_require_approval(monkeypatch):
    entry = _entry()
    db = FakeDB(_lines())
    _wire(monkeypatch, entry, db, False)

    result = service_module.journal_service.post(db, tenant_id=1, entry_id=10, user_id=99, commit=False)

    assert result.status == "posted"
    assert result.total_debit == Decimal("100")
    assert result.total_credit == Decimal("100")
    assert db.flushed
