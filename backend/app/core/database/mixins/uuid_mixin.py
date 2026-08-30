import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class UUIDMixin:
    """
    Adds a globally unique UUID.
    """

    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )