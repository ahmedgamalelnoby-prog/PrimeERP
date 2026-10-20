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



def test_required_branch_policy_blocks_generic_transaction_without_branch(monkeypatch):
    service = transaction_service_module.transaction_service
    monkeypatch.setattr(service, "_get_tenant_id", lambda _user: 3)
    monkeypatch.setattr(service, "_validate_scope", lambda **_kwargs: None)
    monkeypatch.setattr(
        transaction_service_module,
        "get_company_setting",
        lambda _db, _company_id, key: key == "general.branch_required",
    )

    payload = SimpleNamespace(company_id=7, branch_id=None, source_id=None)
    with pytest.raises(HTTPException) as exc:
        service.create_transaction(
            db=object(),
            payload=payload,
            current_user=SimpleNamespace(id=42),
        )

    assert exc.value.status_code == 422
    assert "requires a branch" in exc.value.detail.lower()



def test_disabled_customer_credit_limit_policy_skips_limit_check(monkeypatch):
    from app.modules.commerce import service as commerce_service_module

    service = commerce_service_module.commerce_service
    monkeypatch.setattr(
        commerce_service_module,
        "get_company_setting",
        lambda _db, _company_id, key: False if key == "sales.credit_limit_enforced" else None,
    )
    # If the policy is disabled, no customer lookup or exposure calculation is needed.
    service.enforce_credit_limit(
        db=object(),
        company_id=7,
        document=SimpleNamespace(document_type="invoice", partner_id=10, total=Decimal("500")),
    )



def test_duplicate_customer_policy_blocks_matching_customer(monkeypatch):
    from app.modules.commerce import service as commerce_service_module

    class FakeDB:
        def __init__(self):
            self.calls = 0

        def scalar(self, _query):
            self.calls += 1
            return None if self.calls == 1 else 123

    monkeypatch.setattr(
        commerce_service_module,
        "get_company_setting",
        lambda _db, _company_id, key: key == "crm.duplicate_customer_check",
    )
    payload = SimpleNamespace(
        company_id=7,
        code="C-100",
        partner_type="customer",
        email="same@example.com",
        tax_number=None,
        model_dump=lambda: {},
    )

    with pytest.raises(ValueError, match="Possible duplicate customer"):
        commerce_service_module.commerce_service.create_partner(FakeDB(), payload)



def test_pos_discount_above_no_approval_limit_is_blocked(monkeypatch):
    from app.modules.pos import router as pos_router_module

    monkeypatch.setattr(
        pos_router_module,
        "get_company_setting",
        lambda _db, _company_id, key: {
            "pos.allow_discount_without_approval": True,
            "pos.max_discount_pct_without_approval": 5,
        }[key],
    )
    with pytest.raises(HTTPException) as exc:
        pos_router_module._validate_discount_policy(object(), 7, Decimal("10"))
    assert exc.value.status_code == 409
    assert "maximum" in exc.value.detail.lower()


def test_pos_discount_is_blocked_when_approval_is_required(monkeypatch):
    from app.modules.pos import router as pos_router_module

    monkeypatch.setattr(
        pos_router_module,
        "get_company_setting",
        lambda _db, _company_id, key: {
            "pos.allow_discount_without_approval": False,
            "pos.max_discount_pct_without_approval": 5,
        }[key],
    )
    with pytest.raises(HTTPException) as exc:
        pos_router_module._validate_discount_policy(object(), 7, Decimal("1"))
    assert exc.value.status_code == 409
    assert "requires approval" in exc.value.detail.lower()


def test_pos_discount_within_company_limit_is_allowed(monkeypatch):
    from app.modules.pos import router as pos_router_module

    monkeypatch.setattr(
        pos_router_module,
        "get_company_setting",
        lambda _db, _company_id, key: {
            "pos.allow_discount_without_approval": True,
            "pos.max_discount_pct_without_approval": 5,
        }[key],
    )
    pos_router_module._validate_discount_policy(object(), 7, Decimal("5"))
