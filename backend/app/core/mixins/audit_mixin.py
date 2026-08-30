from typing import Optional

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class AuditMixin:
    @declared_attr
    def created_by(cls) -> Mapped[Optional[int]]:
        return mapped_column(
            Integer,
            ForeignKey(
                "users.id",
                ondelete="SET NULL",
            ),
            nullable=True,
            index=True,
        )

    @declared_attr
    def updated_by(cls) -> Mapped[Optional[int]]:
        return mapped_column(
            Integer,
            ForeignKey(
                "users.id",
                ondelete="SET NULL",
            ),
            nullable=True,
        )