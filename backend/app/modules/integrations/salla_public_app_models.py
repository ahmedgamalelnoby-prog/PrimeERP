from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.database.base import Base


class SallaAppInstallation(Base):
    """Merchant installation state for the public PrimeERP Salla app."""

    __tablename__ = "salla_app_installations"

    id = Column(Integer, primary_key=True)
    merchant_id = Column(String(160), nullable=False, index=True)
    salla_user_id = Column(String(160), nullable=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    connection_id = Column(Integer, ForeignKey("integration_connections.id", ondelete="SET NULL"), nullable=True, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    access_token_ciphertext = Column(Text, nullable=False)
    refresh_token_ciphertext = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    scope = Column(Text, nullable=True)
    token_type = Column(String(30), nullable=False, server_default="bearer")

    store_name = Column(String(255), nullable=True)
    store_domain = Column(String(500), nullable=True)
    merchant_email = Column(String(320), nullable=True)

    status = Column(String(30), nullable=False, server_default="active", index=True)
    subscription_status = Column(String(30), nullable=True, index=True)
    subscription_id = Column(String(160), nullable=True, index=True)
    subscription_item_slug = Column(String(160), nullable=True)
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    last_authorized_at = Column(DateTime(timezone=True), nullable=True)
    last_webhook_at = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(JSON, nullable=False, server_default="{}")

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("merchant_id", name="uq_salla_app_installation_merchant"),
    )


class SallaAppEvent(Base):
    """Durable idempotency ledger for signed Salla public-app events."""

    __tablename__ = "salla_app_events"

    id = Column(Integer, primary_key=True)
    merchant_id = Column(String(160), nullable=False, index=True)
    event_id = Column(String(255), nullable=False)
    event_type = Column(String(160), nullable=False)
    payload_sha256 = Column(String(64), nullable=False)
    status = Column(String(30), nullable=False, server_default="processing", index=True)
    result_json = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("merchant_id", "event_id", name="uq_salla_app_event_merchant_event"),
    )


class SallaSSOTicket(Base):
    """One-time short-lived ticket exchanged by the PrimeERP frontend for a JWT."""

    __tablename__ = "salla_sso_tickets"

    id = Column(String(128), primary_key=True)
    installation_id = Column(Integer, ForeignKey("salla_app_installations.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    consumed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
