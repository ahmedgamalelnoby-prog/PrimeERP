from types import SimpleNamespace

from app.modules.integrations.processor import (
    MAX_ATTEMPTS,
    _failure_status,
    _retry_delay,
    claim_next_event,
    process_one,
)


def test_retry_delay_is_bounded():
    assert _retry_delay(1) == 2
    assert _retry_delay(8) == 256
    assert _retry_delay(20) == 300


def test_failure_status_moves_to_dead_letter_at_limit():
    assert _failure_status(MAX_ATTEMPTS - 1) == "queued"
    assert _failure_status(MAX_ATTEMPTS) == "dead_letter"


def test_claim_next_event_marks_event_processing():
    class FakeDB:
        def scalar(self, _stmt):
            return self.event

        def flush(self):
            return None

    event = SimpleNamespace(status="received", attempts=0, next_attempt_at=None)
    db = FakeDB()
    db.event = event
    claimed = claim_next_event(db)

    assert claimed is event
    assert event.status == "processing"
    assert event.attempts == 1
    assert event.next_attempt_at is None


def test_process_one_success_transitions_to_processed():
    class FakeDB:
        def scalar(self, _stmt):
            return self.event

        def flush(self):
            return None

        def commit(self):
            self.commits += 1

        def rollback(self):
            raise AssertionError("rollback is not expected")

    event = SimpleNamespace(id=1, status="received", attempts=0, next_attempt_at=None, processed_at=None, last_error=None)
    db = FakeDB()
    db.event = event
    db.commits = 0

    result = process_one(db, lambda _event: None)

    assert result is event
    assert event.status == "processed"
    assert event.attempts == 1
    assert event.last_error is None
    assert db.commits == 1


def test_process_one_failure_persists_retry_attempt_after_rollback():
    class FakeDB:
        def scalar(self, _stmt):
            return self.event

        def flush(self):
            return None

        def commit(self):
            self.commits += 1

        def rollback(self):
            self.event.status = "received"
            self.event.attempts = 0
            self.event.next_attempt_at = None

    event = SimpleNamespace(id=2, status="received", attempts=0, next_attempt_at=None, processed_at=None, last_error=None)
    db = FakeDB()
    db.event = event
    db.commits = 0

    def fail(_event):
        raise ValueError("boom")

    result = process_one(db, fail)

    assert result is event
    assert event.attempts == 1
    assert event.status == "queued"
    assert event.last_error == "boom"
    assert event.next_attempt_at is not None
    assert db.commits == 1


def test_process_one_failure_at_limit_persists_dead_letter():
    class FakeDB:
        def scalar(self, _stmt):
            return self.event

        def flush(self):
            return None

        def commit(self):
            self.commits += 1

        def rollback(self):
            self.event.status = "received"
            self.event.attempts = MAX_ATTEMPTS - 1
            self.event.next_attempt_at = None

    event = SimpleNamespace(id=3, status="received", attempts=MAX_ATTEMPTS - 1, next_attempt_at=None, processed_at=None, last_error=None)
    db = FakeDB()
    db.event = event
    db.commits = 0

    def fail(_event):
        raise ValueError("final failure")

    result = process_one(db, fail)

    assert result is event
    assert event.attempts == MAX_ATTEMPTS
    assert event.status == "dead_letter"
    assert event.next_attempt_at is None
    assert db.commits == 1
