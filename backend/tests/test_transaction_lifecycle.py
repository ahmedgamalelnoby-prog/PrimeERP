from app.core.services.transaction_lifecycle import (
    DocumentStatus,
    DuplicateIdempotencyKeyError,
    InvalidTransitionError,
    LifecycleError,
    MissingReasonError,
    PostedDocumentError,
    TransactionDocument,
    TransactionLifecycle,
)


def test_happy_path_is_auditable_and_versioned():
    engine = TransactionLifecycle()
    document = TransactionDocument("sales_order", "SO-1")

    engine.transition(
        document,
        DocumentStatus.PENDING_APPROVAL,
        actor_id="u1",
        idempotency_key="k1",
    )
    engine.approve(document, actor_id="u2", idempotency_key="k2")
    engine.post(document, actor_id="u3", idempotency_key="k3")

    assert document.status == DocumentStatus.POSTED
    assert document.version == 3
    assert document.posted_at is not None
    assert [event.actor_id for event in document.events] == ["u1", "u2", "u3"]


def test_invalid_transition_is_rejected():
    engine = TransactionLifecycle()
    document = TransactionDocument("invoice", "INV-1")

    try:
        engine.post(document, actor_id="u1")
        assert False, "posting a draft must require approval"
    except InvalidTransitionError:
        pass


def test_posted_document_requires_explicit_reversal_reason():
    engine = TransactionLifecycle()
    document = TransactionDocument("invoice", "INV-2")
    engine.approve(document, actor_id="u1")
    engine.post(document, actor_id="u1")

    try:
        engine.transition(document, DocumentStatus.REVERSED, actor_id="u2")
        assert False, "reversal without a reason must fail"
    except MissingReasonError:
        pass

    engine.reverse(document, actor_id="u2", reason="Customer cancellation")
    assert document.status == DocumentStatus.REVERSED


def test_posted_document_cannot_be_cancelled_or_edited_through_transition():
    engine = TransactionLifecycle()
    document = TransactionDocument("payment", "PAY-1")
    engine.approve(document, actor_id="u1")
    engine.post(document, actor_id="u1")

    try:
        engine.transition(document, DocumentStatus.CANCELLED, actor_id="u2")
        assert False
    except InvalidTransitionError:
        pass

    assert document.status == DocumentStatus.POSTED


def test_idempotency_replays_same_event_and_rejects_key_reuse():
    engine = TransactionLifecycle()
    document = TransactionDocument("shipment", "SHP-1")

    first = engine.transition(
        document,
        DocumentStatus.PENDING_APPROVAL,
        actor_id="u1",
        idempotency_key="same-key",
    )
    replay = engine.transition(
        document,
        DocumentStatus.PENDING_APPROVAL,
        actor_id="u1",
        idempotency_key="same-key",
    )
    assert replay is first
    assert document.version == 1

    try:
        engine.transition(
            document,
            DocumentStatus.APPROVED,
            actor_id="u2",
            idempotency_key="same-key",
        )
        assert False
    except DuplicateIdempotencyKeyError:
        pass


def test_cancelled_document_is_terminal():
    engine = TransactionLifecycle()
    document = TransactionDocument("purchase_order", "PO-1")

    engine.transition(document, DocumentStatus.CANCELLED, actor_id="u1")
    assert document.status == DocumentStatus.CANCELLED

    try:
        engine.transition(document, DocumentStatus.DRAFT, actor_id="u2")
        assert False
    except InvalidTransitionError:
        pass


def test_reversal_is_terminal_and_keeps_original_post_timestamp():
    engine = TransactionLifecycle()
    document = TransactionDocument("journal", "JE-1")
    engine.approve(document, actor_id="u1")
    engine.post(document, actor_id="u1")
    posted_at = document.posted_at

    engine.reverse(document, actor_id="u2", reason="Correction")
    assert document.status == DocumentStatus.REVERSED
    assert document.posted_at == posted_at
    assert document.reversed_by == "u2"


def test_blank_actor_is_rejected():
    engine = TransactionLifecycle()
    document = TransactionDocument("invoice", "INV-3")

    try:
        engine.approve(document, actor_id=" ")
        assert False
    except Exception as exc:
        assert "actor_id" in str(exc)



def test_expected_version_prevents_stale_transition():
    engine = TransactionLifecycle()
    document = TransactionDocument("invoice", "INV-V1")
    engine.approve(document, actor_id="u1")

    try:
        engine.post(document, actor_id="u2", expected_version=0)
        assert False
    except LifecycleError as exc:
        assert "Stale transaction version" in str(exc)


class InMemoryPersistentIdempotency:
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def put(self, key, document_id, target):
        self.data[key] = (document_id, target)


def test_injectable_idempotency_store_contract():
    store = InMemoryPersistentIdempotency()
    engine = TransactionLifecycle(idempotency_store=store)
    document = TransactionDocument("invoice", "INV-P1")
    event = engine.approve(document, actor_id="u1", idempotency_key="persistent-key")
    assert store.get("persistent-key") == ("INV-P1", DocumentStatus.APPROVED)
    assert event.to_status == DocumentStatus.APPROVED
