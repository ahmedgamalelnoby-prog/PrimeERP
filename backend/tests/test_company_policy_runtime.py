from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import app.modules.transactions.services.transaction_service as transaction_service_module
from app.modules.accounting.tax_engine import money


def test_company_rounding_policy_modes():
    amount = Decimal("1.005")
    assert money(amount, "half_up") == Decimal("1.01")
    assert money(amount, "bankers") == Decimal("1.00")
    assert money(amount, "none") == Decimal("1.005")


def test_requester_cannot_approve_own_transaction_when_company_policy_disables_it(monkeypatch):
    service = transaction_service_module.transaction_service
    transaction = SimpleNamespace(company_id=7, created_by=42, status="pending")
    monkeypatch.setattr(service, "_get_locked", lambda **_kwargs: transaction)
    monkeypatch.setattr(
        transaction_service_module,
        "get_company_setting",
        lambda _db, _company_id, key: key == "workflow.allow_self_approval",
    )

    with pytest.raises(HTTPException) as exc:
        service.approve_transaction(
            db=object(),
            transaction_id=100,
            current_user=SimpleNamespace(id=42),
        )

    assert exc.value.status_code == 409
    assert "does not allow" in exc.value.detail.lower()
