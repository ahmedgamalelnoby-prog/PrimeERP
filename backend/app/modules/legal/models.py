from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.database.base import Base


class LegalDocument(Base):
    __tablename__ = "legal_documents"

    id = Column(Integer, primary_key=True)
    document_type = Column(String(30), nullable=False, index=True)
    title_ar = Column(String(200), nullable=False)
    title_en = Column(String(200), nullable=False)
    content_ar = Column(Text, nullable=False, default="")
    content_en = Column(Text, nullable=False, default="")
    version = Column(Integer, nullable=False, server_default="1")
    is_published = Column(Boolean, nullable=False, server_default=func.true(), index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("document_type", name="uq_legal_document_type"),
    )


class LegalAcceptance(Base):
    __tablename__ = "legal_acceptances"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String(30), nullable=False, index=True)
    document_version = Column(Integer, nullable=False)
    accepted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "document_type", "document_version", name="uq_legal_acceptance"),
    )
