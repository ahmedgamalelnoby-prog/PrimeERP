from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.database.base import Base


class SallaExternalMapping(Base):
    __tablename__ = "salla_external_mappings"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    connection_id = Column(Integer, ForeignKey("integration_connections.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(40), nullable=False)
    external_id = Column(String(160), nullable=False)
    internal_id = Column(Integer, nullable=True)
    external_version = Column(String(80), nullable=True)
    payload = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            "connection_id", "entity_type", "external_id",
            name="uq_salla_mapping_connection_entity_external",
        ),
    )
