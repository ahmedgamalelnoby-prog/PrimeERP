"""Reusable document lifecycle rules for PrimeERP transactional domains.

The lifecycle engine is persistence-agnostic: domain services own side effects
such as GL, inventory, reservations, payments and notifications.
"""

from dataclasses import dataclass
from typing import Mapping


class LifecycleError(ValueError):
    """Raised when a document attempts an invalid lifecycle transition."""


@dataclass(frozen=True)
class LifecyclePolicy:
    transitions: Mapping[str, frozenset[str]]
    terminal_states: frozenset[str] = frozenset({"cancelled", "reversed"})

    def can_transition(self, current: str, target: str) -> bool:
        return current != target and target in self.transitions.get(
            current, frozenset()
        )

    def validate(self, current: str, target: str) -> None:
        if current in self.terminal_states:
            raise LifecycleError(
                f"Terminal state '{current}' cannot transition to '{target}'"
            )
        if not self.can_transition(current, target):
            raise LifecycleError(
                f"Cannot change document from '{current}' to '{target}'"
            )


TRANSACTION_LIFECYCLE = LifecyclePolicy(
    transitions={
        "draft": frozenset({"pending", "cancelled"}),
        "pending": frozenset({"approved", "cancelled"}),
        "approved": frozenset({"posted", "cancelled"}),
        "posted": frozenset({"reversed"}),
        "reversed": frozenset(),
        "cancelled": frozenset(),
    }
)


def validate_transaction_transition(current: str, target: str) -> None:
    TRANSACTION_LIFECYCLE.validate(current, target)
