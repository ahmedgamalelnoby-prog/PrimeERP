from __future__ import annotations

from app.domain.enums.base import StrEnum


class DocumentStatus(StrEnum):
    """
    Common document lifecycle across PrimeERP.
    """

    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    POSTED = "posted"
    CLOSED = "closed"
    CANCELLED = "cancelled"