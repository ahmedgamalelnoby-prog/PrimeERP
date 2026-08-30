from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class AccountingJournal(Base):
    __tablename__ = "accounting_journals"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    tenant_id = Column(
        Integer,
        ForeignKey(
            "tenants.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey(
            "companies.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    code = Column(
        String(30),
        nullable=False,
    )

    name_ar = Column(
        String(150),
        nullable=False,
    )

    name_en = Column(
        String(150),
        nullable=False,
    )

    journal_type = Column(
        String(30),
        nullable=False,
        default="general",
        index=True,
    )

    sequence_key = Column(
        String(50),
        nullable=False,
        default="JOURNAL_ENTRY",
    )

    description = Column(
        Text,
        nullable=True,
    )

    allow_manual_entries = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    auto_post = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    requires_approval = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    created_by = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    updated_by = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    entries = relationship(
        "JournalEntry",
        back_populates="journal",
        passive_deletes=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "company_id",
            "code",
            name="uq_accounting_journal_scope_code",
        ),
        CheckConstraint(
            "journal_type IN ("
            "'general', "
            "'sales', "
            "'purchase', "
            "'cash', "
            "'bank', "
            "'inventory', "
            "'payroll', "
            "'adjustment', "
            "'opening', "
            "'closing'"
            ")",
            name="ck_accounting_journal_type",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<AccountingJournal "
            f"code={self.code!r} "
            f"type={self.journal_type!r}>"
        )