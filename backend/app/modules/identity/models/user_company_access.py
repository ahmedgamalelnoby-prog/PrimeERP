from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, TIMESTAMP, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class UserCompanyAccess(Base):
    __tablename__ = "user_company_access"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True)
    is_default = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    user = relationship("User", back_populates="company_access")
    company = relationship("Company", back_populates="user_access")

    __table_args__ = (
        Index("uq_user_company_access_default", "user_id", unique=True,
              postgresql_where=text("is_default IS TRUE")),
        Index("ix_user_company_access_company_id", "company_id"),
    )
