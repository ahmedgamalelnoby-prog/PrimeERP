"""Compatibility facade for the universal PrimeERP transaction lifecycle.

The persistence-agnostic engine in app.core.services.transaction_lifecycle is
now the single implementation of transition validation. This module preserves
the legacy string-based API used by the transactions domain.
"""

from dataclasses import dataclass
from typing import Mapping

from app.core.services.transaction_lifecycle import (
    DocumentStatus,
    TransactionDocument,
    TransactionLifecycle,
    LifecycleError as CoreLifecycleError,
)


class LifecycleError(ValueError):
    """Raised when a document attempts an invalid lifecycle transition."""


_STATUS_MAP = {
    "draft": DocumentStatus.DRAFT,
    "pending": DocumentStatus.PENDING_APPROVAL,
    "pending_approval": DocumentStatus.PENDING_APPROVAL,
    "approved": DocumentStatus.APPROVED,
    "posted": DocumentStatus.POSTED,
    "cancelled": DocumentStatus.CANCELLED,
    "reversed": DocumentStatus.REVERSED,
}


# Legacy transaction-domain policy deliberately keeps the existing approval
# gate: draft -> pending -> approved -> posted. The universal engine remains
# responsible for the actual transition algorithm.
TRANSACTION_TRANSITIONS: Mapping[str, frozenset[str]] = {
    "draft": frozenset({"pending", "cancelled"}),
    "pending": frozenset({"approved", "cancelled"}),
    "approved": frozenset({"posted", "cancelled"}),
    "posted": frozenset({"reversed"}),
    "reversed": frozenset(),
    "cancelled": frozenset(),
}


@dataclass(frozen=True)
class LifecyclePolicy:
    transitions: Mapping[str, frozenset[str]]
    terminal_states: frozenset[str] = frozenset({"cancelled", "reversed"})

    def _engine(self) -> TransactionLifecycle:
        core_transitions = {
            _STATUS_MAP[current]: frozenset(
                _STATUS_MAP[target] for target in targets
            )
            for current, targets in self.transitions.items()
        }
        return TransactionLifecycle(transitions=core_transitions)

    def can_transition(self, current: str, target: str) -> bool:
        try:
            self.validate(current, target)
        except LifecycleError:
            return False
        return True

    def validate(self, current: str, target: str) -> None:
        try:
            current_status = _STATUS_MAP[current]
            target_status = _STATUS_MAP[target]
        except KeyError as exc:
            raise LifecycleError(
                f"Unknown transaction lifecycle state: {exc.args[0]!r}"
            ) from exc

        document = TransactionDocument(
            document_type="transaction",
            document_id="validation",
            status=current_status,
        )

        try:
            self._engine().transition(
                document,
                target_status,
                actor_id="lifecycle-validator",
                reason="validation",
            )
        except CoreLifecycleError as exc:
            raise LifecycleError(str(exc)) from exc


TRANSACTION_LIFECYCLE = LifecyclePolicy(
    transitions=TRANSACTION_TRANSITIONS,
)


def validate_transaction_transition(current: str, target: str) -> None:
    TRANSACTION_LIFECYCLE.validate(current, target)
