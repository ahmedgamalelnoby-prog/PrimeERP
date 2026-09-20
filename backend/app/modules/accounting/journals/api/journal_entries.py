from datetime import date

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.accounting.journals.schemas.journal_entry import JournalEntryCreate, JournalEntryResponse, JournalResponse
from app.modules.accounting.journals.services.journal_service import journal_service
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User

router = APIRouter(
    prefix="/accounting/journal-entries",
    tags=["Accounting - Journal Entries"],
    dependencies=[Depends(require_permission("accounting.access"))],
)


class JournalReversalRequest(BaseModel):
    reversal_date: date | None = None
    reason: str = Field(min_length=1, max_length=1000)
    description: str | None = Field(default=None, max_length=2000)


def _tenant_id(current_user: User) -> int:
    return get_effective_tenant_id(current_user)


@router.get("/journals", response_model=list[JournalResponse])
def list_journals(company_id: int = Query(gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return journal_service.list_journals(db, _tenant_id(current_user), company_id)


@router.get("", response_model=list[JournalEntryResponse])
def list_entries(
    company_id: int = Query(gt=0),
    status_filter: str | None = Query(default=None, alias="status"),
    from_date: date | None = None,
    to_date: date | None = None,
    journal_id: int | None = Query(default=None, gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return journal_service.list_entries(db, _tenant_id(current_user), company_id, status=status_filter, start_date=from_date, end_date=to_date, journal_id=journal_id)


@router.get("/{entry_id}", response_model=JournalEntryResponse)
def get_entry(entry_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return journal_service.get_entry(db, _tenant_id(current_user), entry_id)


@router.post("", response_model=JournalEntryResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("accounting.write"))])
def create_entry(payload: JournalEntryCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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


@router.post("/{entry_id}/submit", response_model=JournalEntryResponse, dependencies=[Depends(require_permission("accounting.write"))])
def submit_entry(entry_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return journal_service.submit(db, tenant_id=_tenant_id(current_user), entry_id=entry_id, user_id=current_user.id)


@router.post("/{entry_id}/approve", response_model=JournalEntryResponse, dependencies=[Depends(require_permission("accounting.post"))])
def approve_entry(entry_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return journal_service.approve(db, tenant_id=_tenant_id(current_user), entry_id=entry_id, user_id=current_user.id)


@router.post("/{entry_id}/post", response_model=JournalEntryResponse, dependencies=[Depends(require_permission("accounting.post"))])
def post_entry(entry_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return journal_service.post(db, tenant_id=_tenant_id(current_user), entry_id=entry_id, user_id=current_user.id)


@router.post("/{entry_id}/reverse", response_model=JournalEntryResponse, dependencies=[Depends(require_permission("accounting.post"))])
def reverse_entry(entry_id: int, payload: JournalReversalRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    request = payload
    return journal_service.reverse(
        db,
        tenant_id=_tenant_id(current_user),
        entry_id=entry_id,
        user_id=current_user.id,
        reversal_date=request.reversal_date,
        description=request.description,
        reason=request.reason,
    )


@router.post("/{entry_id}/cancel", response_model=JournalEntryResponse, dependencies=[Depends(require_permission("accounting.write"))])
def cancel_entry(entry_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return journal_service.cancel(db, tenant_id=_tenant_id(current_user), entry_id=entry_id, user_id=current_user.id)
