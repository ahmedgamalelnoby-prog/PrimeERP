from sqlalchemy import Boolean, Column, ForeignKey, Integer, TIMESTAMP, UniqueConstraint
from sqlalchemy.sql import func

from app.database.base import Base


class BranchUserMembership(Base):
    """Explicit user access grant to a branch inside an assigned company."""

    __tablename__ = "branch_user_memberships"

    id = Column(Integer, primary_key=True)
    branch_id = Column(
        Integer,
        ForeignKey("branches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    assigned_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("branch_id", "user_id", name="uq_branch_user_membership"),
    )
