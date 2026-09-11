from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, Text

from app.database.base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    plan_id = Column(Integer, nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(String(50), nullable=True)
    auto_renew = Column(Boolean, nullable=False, default=True)
    quantity = Column(Integer, nullable=False, default=1)
    price = Column(Numeric(18, 2), nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="EGP")
    external_reference = Column(String(100), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
