from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class BranchMixin:
    @declared_attr
    def branch_id(cls) -> Mapped[int]:
        return mapped_column(
            Integer,
            ForeignKey(
                "branches.id",
                ondelete="RESTRICT",
            ),
            nullable=False,
            index=True,
        )