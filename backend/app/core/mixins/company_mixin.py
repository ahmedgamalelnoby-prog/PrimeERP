from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class CompanyMixin:
    @declared_attr
    def company_id(cls) -> Mapped[int]:
        return mapped_column(
            Integer,
            ForeignKey(
                "companies.id",
                ondelete="RESTRICT",
            ),
            nullable=False,
            index=True,
        )