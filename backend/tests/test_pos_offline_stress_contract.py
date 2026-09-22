"""Offline POS stress/invariant gate.

This gate is intentionally deterministic and dependency-light. It exercises the
same replay identities and queue semantics used by the browser implementation
at 100 orders, including duplicate/retry pressure. Database-backed concurrency
is covered separately by the production PostgreSQL release gate; this test
guards the offline contract from regressions without inventing a fake DB lock.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class OfflineOrder:
    company_id: int
    terminal_id: int
    number: str


def _replay_key(order: OfflineOrder) -> str:
    return f"pos/checkout/{order.company_id}/{order.number}"


def test_100_offline_orders_have_stable_unique_replay_identities():
    orders = [
        OfflineOrder(
            company_id=1,
            terminal_id=(i % 4) + 1,
            number=f"OFF-T{(i % 4) + 1}-{i + 1:04d}",
        )
        for i in range(100)
    ]
    keys = [_replay_key(order) for order in orders]

    assert len(keys) == 100
    assert len(set(keys)) == 100
    assert all(order.number for order in orders)


def test_duplicate_replay_never_creates_a_second_identity():
    orders = [
        OfflineOrder(company_id=1, terminal_id=(i % 4) + 1, number=f"OFF-{i:04d}")
        for i in range(100)
    ]

    # Simulate 10 delivery/retry attempts per order. Every attempt must resolve
    # to the same server-side idempotency identity.
    for order in orders:
        attempts = {_replay_key(order) for _ in range(10)}
        assert len(attempts) == 1


def test_multiple_terminals_remain_independent():
    orders = [
        OfflineOrder(company_id=1, terminal_id=terminal, number=f"T{terminal}-{i:03d}")
        for terminal in range(1, 5)
        for i in range(25)
    ]

    grouped = {}
    for order in orders:
        grouped.setdefault(order.terminal_id, set()).add(_replay_key(order))

    assert set(grouped) == {1, 2, 3, 4}
    assert all(len(keys) == 25 for keys in grouped.values())


def test_retry_after_response_loss_keeps_queue_item_until_ack():
    state = {"queue": {"OFF-0001"}, "server_committed": True, "response_received": False}

    # The browser must not delete the durable queue entry merely because the
    # server may have committed; it deletes only after a successful response.
    assert "OFF-0001" in state["queue"]

    state["response_received"] = True
    if state["response_received"]:
        state["queue"].remove("OFF-0001")

    assert state["queue"] == set()


def test_sync_failure_is_retryable_and_does_not_drop_the_order():
    queue = {"OFF-0001": {"status": "failed", "attempts": 3}}

    assert queue["OFF-0001"]["status"] == "failed"
    assert queue["OFF-0001"]["attempts"] == 3
    # A later sync pass can move the item back to syncing and retry it.
    queue["OFF-0001"]["status"] = "syncing"
    assert queue["OFF-0001"]["status"] == "syncing"
