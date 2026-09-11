from types import SimpleNamespace

from app.modules.integrations.salla_adapter import _apply_existing_order_update


def _document(status="confirmed"):
    return SimpleNamespace(status=status, notes="Salla order")


def test_cancelled_event_cancels_order():
    document = _apply_existing_order_update(_document(), {"status": "cancelled"})
    assert document.status == "cancelled"


def test_delivered_event_fulfills_order():
    document = _apply_existing_order_update(_document(), {"status": "delivered"})
    assert document.status == "fulfilled"


def test_lifecycle_cannot_reopen_cancelled_or_fulfilled_order():
    cancelled = _apply_existing_order_update(_document("cancelled"), {"status": "processing"})
    fulfilled = _apply_existing_order_update(_document("fulfilled"), {"status": "processing"})
    assert cancelled.status == "cancelled"
    assert fulfilled.status == "fulfilled"


def test_unknown_salla_status_does_not_corrupt_internal_status():
    document = _apply_existing_order_update(_document("confirmed"), {"status": "unknown_state"})
    assert document.status == "confirmed"
