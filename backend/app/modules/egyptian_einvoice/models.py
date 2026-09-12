from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.database.base import Base


class EgyptianEInvoiceDocument(Base):
    __tablename__ = "egyptian_einvoice_documents"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String(40), nullable=False)
    source_id = Column(Integer, nullable=False, index=True)
    document_type = Column(String(40), nullable=False)
    internal_number = Column(String(100), nullable=False)
    submission_uuid = Column(String(100), nullable=True, index=True)
    eta_uuid = Column(String(100), nullable=True, index=True)
    status = Column(String(30), nullable=False, default="draft", index=True)
    payload_format = Column(String(20), nullable=False, default="json")
    signed_payload = Column(Text, nullable=True)
    eta_response = Column(Text, nullable=True)
    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
