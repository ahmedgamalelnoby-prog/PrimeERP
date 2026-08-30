from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class TransactionEvent(Base):
    __tablename__ = "transaction_events"

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

    transaction_id = Column(
        Integer,
        ForeignKey(
            "business_transactions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    event_type = Column(
        String(50),
        nullable=False,
        index=True,
    )

    previous_status = Column(
        String(30),
        nullable=True,
    )

    new_status = Column(
        String(30),
        nullable=True,
    )

    description = Column(
        Text,
        nullable=True,
    )

    event_data = Column(
        JSON,
        nullable=True,
    )

    performed_by = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    transaction = relationship(
        "BusinessTransaction",
        back_populates="events",
    )

    def __repr__(self) -> str:
        return (
            f"<TransactionEvent "
            f"transaction_id={self.transaction_id} "
            f"type={self.event_type!r}>"
        )