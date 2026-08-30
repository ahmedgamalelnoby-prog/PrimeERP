from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class TenantMixin:
    @declared_attr
    def tenant_id(cls) -> Mapped[int]:
        return mapped_column(
            Integer,
            ForeignKey(
                "tenants.id",
                ondelete="CASCADE",
            ),
            nullable=False,
            index=True,
        )