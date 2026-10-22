from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from app.database.base import Base


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(80), nullable=False)
    entity_id = Column(Integer, nullable=True)
    title = Column(String(240), nullable=False)
    requested_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    mode = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, server_default="pending")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    decided_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("mode IN ('sequential','parallel','any_one')", name="ck_approval_requests_mode"),
        CheckConstraint("status IN ('pending','approved','rejected','cancelled')", name="ck_approval_requests_status"),
    )


class ApprovalStep(Base):
    __tablename__ = "approval_steps"

    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey("approval_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    approver_user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    sequence_no = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, server_default="pending")
    decided_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    reason = Column(Text, nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("request_id", "approver_user_id", name="uq_approval_step_request_approver"),
        UniqueConstraint("request_id", "sequence_no", name="uq_approval_step_request_sequence"),
        CheckConstraint("sequence_no > 0", name="ck_approval_steps_sequence"),
        CheckConstraint("status IN ('pending','approved','rejected','skipped')", name="ck_approval_steps_status"),
    )
