from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Numeric, ForeignKey, UniqueConstraint, Index
from sqlalchemy.sql import func
from app.database.base import Base

class FunctionalTransaction(Base):
    __tablename__ = "functional_transactions"
    id=Column(Integer,primary_key=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    module=Column(String(60),nullable=False,index=True)
    document_type=Column(String(80),nullable=False)
    document_id=Column(String(120),nullable=False)
    status=Column(String(40),nullable=False,default="draft")
    source=Column(String(80),nullable=True)
    idempotency_key=Column(String(180),nullable=False)
    posting_id=Column(String(120),nullable=True)
    reversal_of_id=Column(Integer,ForeignKey("functional_transactions.id",ondelete="SET NULL"),nullable=True)
    reason=Column(Text,nullable=True)
    created_by=Column(Integer,ForeignKey("users.id",ondelete="SET NULL"),nullable=True)
    created_at=Column(DateTime(timezone=True),nullable=False,server_default=func.now())
    updated_at=Column(DateTime(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())
    __table_args__=(UniqueConstraint("tenant_id","module","idempotency_key",name="uq_functional_tx_idempotency"),Index("ix_functional_tx_doc","company_id","module","document_type","document_id"))

class TransactionApproval(Base):
    __tablename__="transaction_approvals"
    id=Column(Integer,primary_key=True)
    transaction_id=Column(Integer,ForeignKey("functional_transactions.id",ondelete="CASCADE"),nullable=False,index=True)
    level=Column(Integer,nullable=False)
    approver_id=Column(Integer,ForeignKey("users.id",ondelete="SET NULL"),nullable=True)
    status=Column(String(20),nullable=False,default="pending")
    decision_reason=Column(Text,nullable=True)
    decided_at=Column(DateTime(timezone=True),nullable=True)
    created_at=Column(DateTime(timezone=True),nullable=False,server_default=func.now())

class PostingDiagnostic(Base):
    __tablename__="posting_diagnostics"
    id=Column(Integer,primary_key=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    module=Column(String(60),nullable=False)
    document_type=Column(String(80),nullable=False)
    document_id=Column(String(120),nullable=False)
    severity=Column(String(20),nullable=False)
    code=Column(String(80),nullable=False)
    message=Column(Text,nullable=False)
    resolved=Column(Boolean,nullable=False,default=False)
    created_at=Column(DateTime(timezone=True),nullable=False,server_default=func.now())

class ReconciliationItem(Base):
    __tablename__="functional_reconciliation_items"
    id=Column(Integer,primary_key=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    reconciliation_type=Column(String(50),nullable=False)
    source_ref=Column(String(160),nullable=False)
    target_ref=Column(String(160),nullable=True)
    source_amount=Column(Numeric(20,6),nullable=True)
    target_amount=Column(Numeric(20,6),nullable=True)
    tolerance=Column(Numeric(20,6),nullable=False,default=0)
    status=Column(String(20),nullable=False,default="unmatched")
    created_at=Column(DateTime(timezone=True),nullable=False,server_default=func.now())

class PeriodControl(Base):
    __tablename__="functional_period_controls"
    id=Column(Integer,primary_key=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    period_key=Column(String(30),nullable=False)
    module=Column(String(60),nullable=False,default="*")
    is_locked=Column(Boolean,nullable=False,default=False)
    reopened_by=Column(Integer,ForeignKey("users.id",ondelete="SET NULL"),nullable=True)
    reopened_at=Column(DateTime(timezone=True),nullable=True)
    reason=Column(Text,nullable=True)
    __table_args__=(UniqueConstraint("company_id","period_key","module",name="uq_functional_period_control"),)
