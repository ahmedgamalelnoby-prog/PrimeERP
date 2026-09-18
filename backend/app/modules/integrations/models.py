from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func
from app.database.base import Base

class IntegrationConnection(Base):
    __tablename__ = "integration_connections"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(40), nullable=False)
    name = Column(String(120), nullable=False)
    base_url = Column(String(300))
    credential_ref = Column(String(200))
    webhook_secret_env = Column(String(200))
    is_active = Column(Boolean, nullable=False, server_default="true")
    last_sync_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    __table_args__ = (UniqueConstraint("company_id", "provider", "name", name="uq_integration_company_provider_name"),)

class IntegrationEvent(Base):
    __tablename__ = "integration_events"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    connection_id = Column(Integer, ForeignKey("integration_connections.id", ondelete="CASCADE"), nullable=False, index=True)
    external_event_id = Column(String(160), nullable=False)
    event_type = Column(String(100), nullable=False)
    payload = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, server_default="received")
    attempts = Column(Integer, nullable=False, server_default="0")
    next_attempt_at = Column(DateTime(timezone=True), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    received_at = Column(DateTime, nullable=False, server_default=func.now())
    __table_args__ = (UniqueConstraint("connection_id", "external_event_id", name="uq_integration_event_external_id"),)

class IntegrationMapping(Base):
    __tablename__ = "integration_mappings"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    connection_id = Column(Integer, ForeignKey("integration_connections.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(40), nullable=False)
    external_id = Column(String(160), nullable=False)
    local_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    __table_args__ = (
        UniqueConstraint("connection_id", "entity_type", "external_id", name="uq_integration_mapping_external"),
        UniqueConstraint("connection_id", "entity_type", "local_id", name="uq_integration_mapping_local"),
    )

class IntegrationProductMapping(Base):
    __tablename__ = "integration_product_mappings"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    connection_id = Column(Integer, ForeignKey("integration_connections.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False)
    catalog_product_id = Column(Integer, ForeignKey("catalog_products.id", ondelete="RESTRICT"), nullable=True, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=True)
    entity_type = Column(String(20), nullable=False, server_default="product")
    external_id = Column(String(160), nullable=False)
    external_sku = Column(String(160), nullable=True)
    external_url = Column(String(500), nullable=True)
    sync_direction = Column(String(20), nullable=False, server_default="bidirectional")
    sync_status = Column(String(20), nullable=False, server_default="active")
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    __table_args__ = (
        UniqueConstraint("connection_id", "entity_type", "external_id", name="uq_integration_product_mapping_external"),
        Index("uq_integration_product_mapping_local_variant", "connection_id", "product_id", "variant_id", unique=True, postgresql_where=variant_id.is_not(None)),
        Index("uq_integration_product_mapping_local_product", "connection_id", "product_id", unique=True, postgresql_where=variant_id.is_(None)),
        Index("ix_integration_product_mapping_connection_entity_external", "connection_id", "entity_type", "external_id"),
    )
