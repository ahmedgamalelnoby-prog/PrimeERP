from decimal import Decimal
from types import SimpleNamespace

from app.modules.treasury.accounting_service import TreasuryAccountingService


def _settings():
    return SimpleNamespace(
        received_cheques_account_id=10,
        under_collection_account_id=11,
        returned_cheques_account_id=12,
        issued_cheques_account_id=13,
        bank_account_id=14,
    )


def _commerce():
    return SimpleNamespace(ar_account_id=20, ap_account_id=21)


def _cheque(direction="received", status="received"):
    return SimpleNamespace(direction=direction, status=status, amount=Decimal("100.00"), cheque_number="CH-1")


def _event(event_type, before=None, after="received"):
    return SimpleNamespace(event_type=event_type, from_status=before, to_status=after)


def _assert_balanced(lines):
    assert sum(Decimal(str(x["debit"])) for x in lines) == sum(Decimal(str(x["credit"])) for x in lines) == Decimal("100.00")


def test_received_cheque_lifecycle_accounting_is_balanced():
    service = TreasuryAccountingService(); s = _settings(); c = _commerce()
    for event, before, after, status in [
        ("created", None, "received", "received"),
        ("deposited", "received", "deposited", "deposited"),
        ("under_collection", "deposited", "under_collection", "under_collection"),
        ("collected", "under_collection", "collected", "collected"),
    ]:
        lines = service._lines_for_event(c, s, _cheque(status=status), _event(event, before, after))
        _assert_balanced(lines)


def test_return_resubmit_and_withdraw_have_explicit_accounts():
    service = TreasuryAccountingService(); s = _settings(); c = _commerce()
    _assert_balanced(service._lines_for_event(c, s, _cheque(status="returned"), _event("returned", "under_collection", "returned")))
    _assert_balanced(service._lines_for_event(c, s, _cheque(status="resubmitted"), _event("resubmitted", "returned", "resubmitted")))
    _assert_balanced(service._lines_for_event(c, s, _cheque(status="received"), _event("withdrawn", "received", "withdrawn")))


def test_issued_cheque_and_clearing_are_balanced():
    service = TreasuryAccountingService(); s = _settings(); c = _commerce()
    _assert_balanced(service._lines_for_event(c, s, _cheque("issued", "issued"), _event("created", None, "issued")))
    _assert_balanced(service._lines_for_event(c, s, _cheque("issued", "cleared"), _event("cleared", "issued", "cleared")))


def test_reversal_reverses_the_last_financial_effect():
    service = TreasuryAccountingService(); s = _settings(); c = _commerce()
    _assert_balanced(service._lines_for_event(c, s, _cheque("issued", "reversed"), _event("reversed", "cleared", "reversed")))
    _assert_balanced(service._lines_for_event(c, s, _cheque(status="reversed"), _event("reversed", "collected", "reversed")))
