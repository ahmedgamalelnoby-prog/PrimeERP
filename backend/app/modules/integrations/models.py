"""Durable integration persistence models.

IntegrationEvent stores asynchronous delivery state. IntegrationMapping keeps a
provider-neutral mapping between an external entity and its PrimeERP entity.
"""
from sqlalchemy import Column, DateTime, Integer, JSON, String, Text, UniqueConstraint, func
from app.database.base import Base


class IntegrationEvent(Base):
    __tablename__ = "integration_events"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, nullable=True, index=True)
    event_type = Column(
        String(120), nullable=False, default="generic", server_default="generic"
    )
    external_id = Column(String(255), nullable=True, index=True)
    payload = Column(JSON, nullable=False, default=dict)
    status = Column(
        String(30), nullable=False, default="received", server_default="received", index=True
    )
    attempts = Column(Integer, nullable=False, default=0, server_default="0")
    next_attempt_at = Column(DateTime(timezone=True), nullable=True, index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class IntegrationMapping(Base):
    """Maps an external integration identity to a local entity identity."""

    __tablename__ = "integration_mappings"
    __table_args__ = (
        UniqueConstraint(
            "company_id", "connection_id", "entity_type", "external_id",
            name="uq_integration_mappings_external_identity",
        ),
    )

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, nullable=False, index=True)
    connection_id = Column(Integer, nullable=False, index=True)
    entity_type = Column(String(120), nullable=False, index=True)
    external_id = Column(String(255), nullable=False, index=True)
    local_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
