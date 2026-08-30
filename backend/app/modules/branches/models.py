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


class Branch(Base):
    __tablename__ = "branches"

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

    company_id = Column(
        Integer,
        ForeignKey(
            "companies.id",
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
        back_populates="branches",
        foreign_keys=[tenant_id],
    )

    company = relationship(
        "Company",
        back_populates="branches",
        foreign_keys=[company_id],
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "company_id",
            "code",
            name="uq_branches_tenant_company_code",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Branch "
            f"id={self.id} "
            f"tenant_id={self.tenant_id} "
            f"company_id={self.company_id} "
            f"name={self.name!r}>"
        )