from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Mapping


class LifecycleError(ValueError):
    """Base error for universal transaction lifecycle violations."""


class InvalidTransitionError(LifecycleError):
    pass


class PostedDocumentError(LifecycleError):
    pass


class DuplicateIdempotencyKeyError(LifecycleError):
    pass


class MissingReasonError(LifecycleError):
    pass


class DocumentStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    POSTED = "posted"
    CANCELLED = "cancelled"
    REVERSED = "reversed"


@dataclass(frozen=True)
class LifecycleEvent:
    document_type: str
    document_id: str
    from_status: DocumentStatus
    to_status: DocumentStatus
    actor_id: str
    occurred_at: datetime
    reason: str | None = None
    idempotency_key: str | None = None


@dataclass
class TransactionDocument:
    document_type: str
    document_id: str
    status: DocumentStatus = DocumentStatus.DRAFT
    version: int = 0
    posted_at: datetime | None = None
    reversed_by: str | None = None
    events: list[LifecycleEvent] = field(default_factory=list)


TransitionGuard = Callable[[TransactionDocument, str], None]


class TransactionLifecycle:
    """Provider-neutral lifecycle state machine for transactional ERP documents.

    Persistence, authorization, audit storage, and accounting posting remain
    adapters. Every adapter can use the same transition contract.
    """

    DEFAULT_TRANSITIONS: Mapping[DocumentStatus, frozenset[DocumentStatus]] = {
        DocumentStatus.DRAFT: frozenset(
            {
                DocumentStatus.PENDING_APPROVAL,
                DocumentStatus.APPROVED,
                DocumentStatus.CANCELLED,
            }
        ),
        DocumentStatus.PENDING_APPROVAL: frozenset(
            {DocumentStatus.APPROVED, DocumentStatus.CANCELLED}
        ),
        DocumentStatus.APPROVED: frozenset(
            {DocumentStatus.POSTED, DocumentStatus.CANCELLED}
        ),
        DocumentStatus.POSTED: frozenset({DocumentStatus.REVERSED}),
        DocumentStatus.CANCELLED: frozenset(),
        DocumentStatus.REVERSED: frozenset(),
    }

    def __init__(
        self,
        *,
        transitions: Mapping[
            DocumentStatus, frozenset[DocumentStatus]
        ] | None = None,
        guards: Mapping[
            tuple[DocumentStatus, DocumentStatus], tuple[TransitionGuard, ...]
        ] | None = None,
    ) -> None:
        self._transitions = transitions or self.DEFAULT_TRANSITIONS
        self._guards = guards or {}
        self._idempotency: dict[str, tuple[str, DocumentStatus]] = {}

    def transition(
        self,
        document: TransactionDocument,
        target: DocumentStatus,
        *,
        actor_id: str,
        reason: str | None = None,
        idempotency_key: str | None = None,
    ) -> LifecycleEvent:
        if not actor_id.strip():
            raise LifecycleError("actor_id is required")

        if idempotency_key:
            prior = self._idempotency.get(idempotency_key)
            if prior:
                if prior != (document.document_id, target):
                    raise DuplicateIdempotencyKeyError(
                        f"Idempotency key {idempotency_key!r} was already used "
                        "for another transition."
                    )
                for event in reversed(document.events):
                    if event.idempotency_key == idempotency_key:
                        return event

        current = document.status
        if target not in self._transitions.get(current, frozenset()):
            raise InvalidTransitionError(
                f"Cannot change {document.document_type} {document.document_id} "
                f"from {current.value} to {target.value}"
            )

        if current == DocumentStatus.POSTED and target == DocumentStatus.REVERSED:
            if not reason or not reason.strip():
                raise MissingReasonError("A reversal reason is required.")

        if current in {
            DocumentStatus.POSTED,
            DocumentStatus.REVERSED,
            DocumentStatus.CANCELLED,
        }:
            raise PostedDocumentError(
                f"{current.value} documents are immutable except explicit reversal."
            )

        if target == DocumentStatus.POSTED and not reason:
            reason = "posted"

        for guard in self._guards.get((current, target), ()):
            guard(document, actor_id)

        now = datetime.now(timezone.utc)
        event = LifecycleEvent(
            document_type=document.document_type,
            document_id=document.document_id,
            from_status=current,
            to_status=target,
            actor_id=actor_id,
            occurred_at=now,
            reason=reason,
            idempotency_key=idempotency_key,
        )
        document.status = target
        document.version += 1
        document.events.append(event)

        if target == DocumentStatus.POSTED:
            document.posted_at = now
        elif target == DocumentStatus.REVERSED:
            document.reversed_by = actor_id

        if idempotency_key:
            self._idempotency[idempotency_key] = (document.document_id, target)

        return event

    def approve(
        self,
        document: TransactionDocument,
        *,
        actor_id: str,
        idempotency_key: str | None = None,
    ) -> LifecycleEvent:
        return self.transition(
            document,
            DocumentStatus.APPROVED,
            actor_id=actor_id,
            idempotency_key=idempotency_key,
        )

    def post(
        self,
        document: TransactionDocument,
        *,
        actor_id: str,
        idempotency_key: str | None = None,
    ) -> LifecycleEvent:
        return self.transition(
            document,
            DocumentStatus.POSTED,
            actor_id=actor_id,
            idempotency_key=idempotency_key,
        )

    def reverse(
        self,
        document: TransactionDocument,
        *,
        actor_id: str,
        reason: str,
        idempotency_key: str | None = None,
    ) -> LifecycleEvent:
        return self.transition(
            document,
            DocumentStatus.REVERSED,
            actor_id=actor_id,
            reason=reason,
            idempotency_key=idempotency_key,
        )
