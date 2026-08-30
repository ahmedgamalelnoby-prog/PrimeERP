from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class BusinessTransaction(Base):
    __tablename__ = "business_transactions"

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
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    branch_id = Column(
        Integer,
        ForeignKey(
            "branches.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    transaction_number = Column(
        String(100),
        nullable=False,
        index=True,
    )

    transaction_type = Column(
        String(80),
        nullable=False,
        index=True,
    )

    document_number = Column(
        String(100),
        nullable=True,
        index=True,
    )

    status = Column(
        String(30),
        nullable=False,
        default="draft",
        index=True,
    )

    source_module = Column(
        String(80),
        nullable=False,
        index=True,
    )

    source_entity = Column(
        String(100),
        nullable=False,
    )

    source_id = Column(
        Integer,
        nullable=True,
        index=True,
    )

    reference_number = Column(
        String(150),
        nullable=True,
        index=True,
    )

    external_reference = Column(
        String(150),
        nullable=True,
        index=True,
    )

    transaction_date = Column(
        Date,
        nullable=False,
    )

    posting_date = Column(
        Date,
        nullable=True,
    )

    original_transaction_id = Column(
        Integer,
        ForeignKey(
            "business_transactions.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )

    reversal_transaction_id = Column(
        Integer,
        ForeignKey(
            "business_transactions.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )

    cancellation_reason = Column(
        Text,
        nullable=True,
    )

    metadata_json = Column(
        JSON,
        nullable=True,
    )

    is_cancelled = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_reversed = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_by = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    approved_by = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    posted_by = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    cancelled_by = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    approved_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    posted_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    cancelled_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    events = relationship(
        "TransactionEvent",
        back_populates="transaction",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="TransactionEvent.created_at",
    )

    original_transaction = relationship(
        "BusinessTransaction",
        remote_side=[id],
        foreign_keys=[original_transaction_id],
        post_update=True,
    )

    reversal_transaction = relationship(
        "BusinessTransaction",
        remote_side=[id],
        foreign_keys=[reversal_transaction_id],
        post_update=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "transaction_number",
            name="uq_business_transaction_number",
        ),
        Index(
            "ix_business_transaction_lookup",
            "tenant_id",
            "company_id",
            "branch_id",
            "transaction_type",
            "status",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<BusinessTransaction "
            f"number={self.transaction_number!r} "
            f"status={self.status!r}>"
        )