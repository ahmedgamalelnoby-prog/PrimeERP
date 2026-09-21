"""Integration event persistence model used by the asynchronous delivery processor."""
from sqlalchemy import Column, DateTime, Integer, JSON, String, Text, func
from app.database.base import Base


class IntegrationEvent(Base):
    __tablename__ = "integration_events"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, nullable=True, index=True)
    event_type = Column(String(120), nullable=False, default="generic")
    external_id = Column(String(255), nullable=True, index=True)
    payload = Column(JSON, nullable=False, default=dict)
    status = Column(String(30), nullable=False, default="received", index=True)
    attempts = Column(Integer, nullable=False, default=0)
    next_attempt_at = Column(DateTime(timezone=True), nullable=True, index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
