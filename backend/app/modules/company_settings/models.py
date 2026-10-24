from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint, func
from app.database.base import Base


class CompanySetting(Base):
    __tablename__ = "company_settings"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    setting_key = Column(String(120), nullable=False)
    value_json = Column(JSON, nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("company_id", "setting_key", name="uq_company_settings_company_key"),)
