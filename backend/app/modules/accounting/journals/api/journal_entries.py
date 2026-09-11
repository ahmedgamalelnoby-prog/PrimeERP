from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.accounting.journals.schemas.journal_entry import (
    JournalEntryCreate,
    JournalEntryResponse,
)
from app.modules.accounting.journals.services.journal_service import journal_service


router = APIRouter(prefix="/accounting/journal-entries", tags=["Accounting - Journal Entries"])


def _tenant_id(current_user: User) -> int:
    if current_user.tenant_id is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not assigned to a tenant")
    return current_user.tenant_id


@router.get("", response_model=list[JournalEntryResponse])
def list_entries(
    company_id: int = Query(gt=0),
    status_filter: str | None = Query(default=None, alias="status"),
    from_date: date | None = None,
    to_date: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return journal_service.list_entries(
        db,
        _tenant_id(current_user),
        company_id,
        status=status_filter,
        from_date=from_date,
        to_date=to_date,
    )


@router.get("/{entry_id}", response_model=JournalEntryResponse)
def get_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return journal_service.get_entry(db, _tenant_id(current_user), entry_id)


@router.post("", response_model=JournalEntryResponse, status_code=status.HTTP_201_CREATED)
def create_entry(
    payload: JournalEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return journal_service.create_draft(
        db,
        tenant_id=_tenant_id(current_user),
        company_id=payload.company_id,
        branch_id=payload.branch_id,
        journal_id=payload.journal_id,
        fiscal_year_id=payload.fiscal_year_id,
        period_id=payload.period_id,
        entry_number=payload.entry_number,
        entry_date=payload.entry_date,
        description=payload.description,
        lines=[line.model_dump() for line in payload.lines],
        user_id=current_user.id,
        currency_code=payload.currency_code,
        exchange_rate=payload.exchange_rate,
        reference=payload.reference,
        source_module=payload.source_module,
        source_entity=payload.source_entity,
        source_id=payload.source_id,
    )


@router.post("/{entry_id}/submit", response_model=JournalEntryResponse)
def submit_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return journal_service.submit(db, tenant_id=_tenant_id(current_user), entry_id=entry_id, user_id=current_user.id)


@router.post("/{entry_id}/approve", response_model=JournalEntryResponse)
def approve_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return journal_service.approve(db, tenant_id=_tenant_id(current_user), entry_id=entry_id, user_id=current_user.id)


@router.post("/{entry_id}/post", response_model=JournalEntryResponse)
def post_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return journal_service.post(db, tenant_id=_tenant_id(current_user), entry_id=entry_id, user_id=current_user.id)


@router.post("/{entry_id}/cancel", response_model=JournalEntryResponse)
def cancel_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return journal_service.cancel(db, tenant_id=_tenant_id(current_user), entry_id=entry_id, user_id=current_user.id)
