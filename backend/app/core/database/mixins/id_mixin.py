from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column


class IdMixin:
    """
    Adds an auto-increment integer primary key.
    """

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
    )