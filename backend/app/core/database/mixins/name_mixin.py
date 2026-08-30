from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class NameMixin:
    """
    Standard entity names.
    """

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    name_ar: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )