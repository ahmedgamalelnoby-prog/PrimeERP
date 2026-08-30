from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column


class AuditMixin:
    """
    Created by / Updated by.
    """

    created_by: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    updated_by: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )