from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column


class DescriptionMixin:
    """
    Optional description.
    """

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )