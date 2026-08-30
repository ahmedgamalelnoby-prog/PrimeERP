from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    TIMESTAMP,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    tenant_id = Column(
        Integer,
        ForeignKey(
            "tenants.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    name = Column(
        String(150),
        nullable=False,
        index=True,
    )

    code = Column(
        String(30),
        nullable=True,
        index=True,
    )

    description = Column(
        Text,
        nullable=True,
    )

    address = Column(
        Text,
        nullable=True,
    )

    phone = Column(
        String(30),
        nullable=True,
    )

    email = Column(
        String(150),
        nullable=True,
    )

    tax_id = Column(
        String(100),
        nullable=True,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    tenant = relationship(
        "Tenant",
        back_populates="companies",
        foreign_keys=[tenant_id],
    )

    branches = relationship(
        "Branch",
        back_populates="company",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="Branch.company_id",
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "code",
            name="uq_companies_tenant_code",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Company "
            f"id={self.id} "
            f"tenant_id={self.tenant_id} "
            f"name={self.name!r}>"
        )