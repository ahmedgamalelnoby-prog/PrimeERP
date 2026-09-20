from app.modules.transactions.lifecycle import (
    LifecycleError,
    LifecyclePolicy,
    validate_transaction_transition,
)


def test_transaction_lifecycle_allows_expected_forward_flow():
    for current, target in (
        ("draft", "pending"),
        ("pending", "approved"),
        ("approved", "posted"),
        ("posted", "reversed"),
    ):
        validate_transaction_transition(current, target)


def test_transaction_lifecycle_rejects_skipping_states():
    try:
        validate_transaction_transition("draft", "posted")
    except LifecycleError:
        return
    raise AssertionError("draft -> posted must require approval")


def test_transaction_lifecycle_rejects_terminal_state_mutation():
    try:
        validate_transaction_transition("cancelled", "draft")
    except LifecycleError:
        return
    raise AssertionError("cancelled documents are immutable")


def test_custom_policy_is_supported():
    policy = LifecyclePolicy(
        transitions={
            "draft": frozenset({"confirmed"}),
            "confirmed": frozenset({"closed"}),
            "closed": frozenset(),
        },
        terminal_states=frozenset({"closed"}),
    )
    policy.validate("draft", "confirmed")
    try:
        policy.validate("closed", "draft")
    except LifecycleError:
        return
    raise AssertionError("custom terminal state must be immutable")
