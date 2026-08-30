from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from app.database.base import Base


class NumberSequence(Base):
    __tablename__ = "number_sequences"

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
        nullable=True,
        index=True,
    )

    branch_id = Column(
        Integer,
        ForeignKey(
            "branches.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    sequence_key = Column(
        String(50),
        nullable=False,
        index=True,
    )

    prefix = Column(
        String(20),
        nullable=False,
        default="TRX",
    )

    format_pattern = Column(
        String(150),
        nullable=False,
        default="{PREFIX}-{YEAR}-{BRANCH}-{SEQ}",
    )

    current_value = Column(
        Integer,
        nullable=False,
        default=0,
    )

    padding = Column(
        Integer,
        nullable=False,
        default=8,
    )

    reset_period = Column(
        String(20),
        nullable=False,
        default="yearly",
    )

    last_reset_year = Column(
        Integer,
        nullable=True,
    )

    last_reset_month = Column(
        Integer,
        nullable=True,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "company_id",
            "branch_id",
            "sequence_key",
            name="uq_number_sequence_scope",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<NumberSequence "
            f"key={self.sequence_key!r} "
            f"value={self.current_value}>"
        )