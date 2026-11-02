from datetime import datetime, timezone
from types import SimpleNamespace

from app.modules.integrations.processor import _retry_delay, claim_next_event


def test_retry_delay_is_bounded():
    assert _retry_delay(1) == 2
    assert _retry_delay(8) == 256
    assert _retry_delay(20) == 300


def test_claim_next_event_marks_event_processing():
    class FakeScalar:
        def __init__(self, event):
            self.event = event

        def scalar(self, _stmt):
            return self.event

    event = SimpleNamespace(
        status="received",
        attempts=0,
        next_attempt_at=None,
    )
    db = FakeScalar(event)
    claimed = claim_next_event(db)
    assert claimed is event
    assert event.status == "processing"
    assert event.attempts == 1
    assert event.next_attempt_at is None
