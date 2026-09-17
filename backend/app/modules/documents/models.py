from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from app.database.base import Base


class DocumentFolder(Base):
    __tablename__ = "document_folders"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("document_folders.id", ondelete="SET NULL"))
    name = Column(String(180), nullable=False)
    access_mode = Column(String(20), nullable=False, server_default="private")
    active = Column(Boolean, nullable=False, server_default="true")


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    folder_id = Column(Integer, ForeignKey("document_folders.id", ondelete="SET NULL"), index=True)
    name = Column(String(240), nullable=False)
    document_type = Column(String(80), nullable=False, server_default="file")
    external_key = Column(String(180))
    storage_uri = Column(Text)
    version_no = Column(Integer, nullable=False, server_default="1")
    access_mode = Column(String(20), nullable=False, server_default="private")
    status = Column(String(20), nullable=False, server_default="active")
    linked_model = Column(String(120))
    linked_record_id = Column(String(120))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_no = Column(Integer, nullable=False)
    storage_uri = Column(Text, nullable=False)
    checksum = Column(String(128))
    created_by_ref = Column(String(120))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")


class DocumentShare(Base):
    __tablename__ = "document_shares"
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    grantee_ref = Column(String(120), primary_key=True)
    role = Column(String(20), nullable=False, server_default="viewer")
    expires_at = Column(DateTime(timezone=True))
    active = Column(Boolean, nullable=False, server_default="true")


class DocumentRequest(Base):
    __tablename__ = "document_requests"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"))
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_from_ref = Column(String(120), nullable=False)
    requested_by_ref = Column(String(120), nullable=False)
    document_name = Column(String(240), nullable=False)
    due_at = Column(DateTime(timezone=True))
    status = Column(String(20), nullable=False, server_default="requested")
    message = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")
