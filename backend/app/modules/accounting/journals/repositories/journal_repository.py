from datetime import date
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.modules.accounting.journals.models import (
    AccountingJournal,
    JournalEntry,
)


class JournalRepository:
    """Tenant-scoped persistence boundary for journals and entries."""

    def get_journal(
        self,
        db: Session,
        journal_id: int,
        tenant_id: int,
        company_id: int,
    ) -> Optional[AccountingJournal]:
        return (
            db.query(AccountingJournal)
            .filter(
                AccountingJournal.id == journal_id,
                AccountingJournal.tenant_id == tenant_id,
                AccountingJournal.company_id == company_id,
            )
            .first()
        )

    def list_journals(
        self,
        db: Session,
        tenant_id: int,
        company_id: int,
        active_only: bool = True,
    ) -> list[AccountingJournal]:
        query = db.query(AccountingJournal).filter(
            AccountingJournal.tenant_id == tenant_id,
            AccountingJournal.company_id == company_id,
        )
        if active_only:
            query = query.filter(AccountingJournal.is_active.is_(True))
        return query.order_by(AccountingJournal.code).all()

    def get_entry(
        self,
        db: Session,
        entry_id: int,
        tenant_id: int,
        for_update: bool = False,
    ) -> Optional[JournalEntry]:
        query = (
            db.query(JournalEntry)
            .options(joinedload(JournalEntry.lines))
            .filter(
                JournalEntry.id == entry_id,
                JournalEntry.tenant_id == tenant_id,
            )
        )
        if for_update:
            query = query.with_for_update()
        return query.first()

    def list_entries(
        self,
        db: Session,
        tenant_id: int,
        company_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[str] = None,
        journal_id: Optional[int] = None,
    ) -> list[JournalEntry]:
        query = (
            db.query(JournalEntry)
            .options(joinedload(JournalEntry.lines))
            .filter(
                JournalEntry.tenant_id == tenant_id,
                JournalEntry.company_id == company_id,
            )
        )
        if start_date is not None:
            query = query.filter(JournalEntry.entry_date >= start_date)
        if end_date is not None:
            query = query.filter(JournalEntry.entry_date <= end_date)
        if status is not None:
            query = query.filter(JournalEntry.status == status)
        if journal_id is not None:
            query = query.filter(JournalEntry.journal_id == journal_id)
        return query.order_by(JournalEntry.entry_date.desc(), JournalEntry.id.desc()).all()


journal_repository = JournalRepository()
