from datetime import date, datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.modules.commerce.models import BusinessPartner
from app.modules.treasury.models import Cheque, ChequeEvent
from app.modules.accounting.fiscal_years.services.fiscal_year_service import fiscal_year_service
from app.modules.treasury.accounting_service import treasury_accounting_service


ALLOWED_TRANSITIONS = {
    "received": {"deposited", "under_collection", "cancelled", "withdrawn"},
    "deposited": {"under_collection", "collected", "returned", "cancelled", "withdrawn"},
    "under_collection": {"collected", "returned", "cancelled", "withdrawn"},
    "returned": {"resubmitted", "cancelled", "withdrawn"},
    "resubmitted": {"deposited", "under_collection", "collected", "returned", "cancelled", "withdrawn"},
    "issued": {"cleared", "cancelled", "reversed", "withdrawn"},
    "cleared": {"reversed"},
    "collected": {"reversed"},
    "withdrawn": set(),
    "cancelled": set(),
    "reversed": set(),
}


def _record_event(db: Session, cheque: Cheque, old_status: str | None, new_status: str, event_type: str, event_date: date, user_id: int | None, reference: str | None, notes: str | None):
    cheque.status = new_status
    cheque.updated_at = datetime.now(timezone.utc)
    db.add(ChequeEvent(company_id=cheque.company_id, cheque_id=cheque.id, event_type=event_type, from_status=old_status, to_status=new_status, event_date=event_date, reference=reference, notes=notes, created_by=user_id, created_at=datetime.now(timezone.utc)))


def create_cheque(db: Session, payload, user_id: int):
    if hasattr(fiscal_year_service, "assert_open_for_date"):
        fiscal_year_service.assert_open_for_date(db, company_id=payload.company_id, posting_date=payload.cheque_date)
    if payload.due_date < payload.cheque_date:
        raise ValueError("Due date cannot be earlier than cheque date")
    if payload.direction not in {"received", "issued"}:
        raise ValueError("Direction must be received or issued")
    if payload.partner_id is not None:
        partner = db.scalar(select(BusinessPartner).where(BusinessPartner.id == payload.partner_id, BusinessPartner.company_id == payload.company_id))
        if partner is None:
            raise ValueError("Partner does not belong to the company")
    status = "received" if payload.direction == "received" else "issued"
    now = datetime.now(timezone.utc)
    cheque = Cheque(**payload.model_dump(), status=status, created_at=now, updated_at=now)
    db.add(cheque)
    db.flush()
    _record_event(db, cheque, None, status, "created", payload.cheque_date, user_id, None, payload.notes)
    treasury_accounting_service.created(db, cheque, user_id)
    return cheque


def transition_cheque(db: Session, cheque: Cheque, new_status: str, action_date: date, user_id: int, event_type: str, reference: str | None, notes: str | None):
    if hasattr(fiscal_year_service, "assert_open_for_date"):
        fiscal_year_service.assert_open_for_date(db, company_id=cheque.company_id, posting_date=action_date)
    locked = db.scalar(select(Cheque).where(Cheque.id == cheque.id, Cheque.company_id == cheque.company_id).with_for_update())
    if locked is None:
        raise ValueError("Cheque not found")
    if new_status not in ALLOWED_TRANSITIONS.get(locked.status, set()):
        raise ValueError(f"Cannot move cheque from {locked.status} to {new_status}")
    old_status = locked.status
    _record_event(db, locked, old_status, new_status, event_type, action_date, user_id, reference, notes)
    if new_status in {"returned", "cancelled", "reversed", "withdrawn"} and old_status not in {"returned", "cancelled", "reversed", "withdrawn"}:
        treasury_accounting_service.cancellation(db, locked, when=action_date, user_id=user_id, event_key=f"{event_type}-{action_date.isoformat()}")
    return locked


def withdraw_cheque(db: Session, cheque: Cheque, action_date: date, user_id: int, reference: str | None, notes: str | None):
    locked = db.scalar(select(Cheque).where(Cheque.id == cheque.id, Cheque.company_id == cheque.company_id).with_for_update())
    if locked is None:
        raise ValueError("Cheque not found")
    if locked.cheque_date < action_date and locked.due_date < action_date:
        raise ValueError("Cheque cannot be withdrawn after both cheque date and due date have passed")
    return transition_cheque(db, locked, "withdrawn", action_date, user_id, "withdrawn", reference, notes)


def resubmit_returned_cheque(db: Session, cheque: Cheque, action_date: date, user_id: int, reference: str | None, notes: str | None):
    locked = db.scalar(select(Cheque).where(Cheque.id == cheque.id, Cheque.company_id == cheque.company_id).with_for_update())
    if locked is None:
        raise ValueError("Cheque not found")
    if locked.status != "returned":
        raise ValueError("Only returned cheques can be resubmitted")
    return transition_cheque(db, locked, "resubmitted", action_date, user_id, "resubmitted", reference, notes)


def list_cheques(db: Session, company_id: int, status: str | None = None, direction: str | None = None):
    stmt = select(Cheque).where(Cheque.company_id == company_id).order_by(Cheque.due_date, Cheque.id)
    if status:
        stmt = stmt.where(Cheque.status == status)
    if direction:
        stmt = stmt.where(Cheque.direction == direction)
    return list(db.scalars(stmt).all())


def events(db: Session, company_id: int, cheque_id: int):
    return list(db.scalars(select(ChequeEvent).where(ChequeEvent.company_id == company_id, ChequeEvent.cheque_id == cheque_id).order_by(ChequeEvent.id)).all())


def endorse_cheque(db: Session, cheque: Cheque, action_date: date, user_id: int, reference: str | None, notes: str | None):
    locked = db.scalar(select(Cheque).where(Cheque.id == cheque.id, Cheque.company_id == cheque.company_id).with_for_update())
    if locked is None: raise ValueError("Cheque not found")
    if locked.direction != "received": raise ValueError("Only incoming cheques can be endorsed")
    if locked.status in {"cancelled","reversed","withdrawn","returned"}: raise ValueError("Cheque is not endorsable in its current status")
    _record_event(db, locked, locked.status, locked.status, "endorsed", action_date, user_id, reference, notes)
    return locked


def replace_cheque(db: Session, cheque: Cheque, replacement, action_date: date, user_id: int):
    locked = db.scalar(select(Cheque).where(Cheque.id == cheque.id, Cheque.company_id == cheque.company_id).with_for_update())
    if locked is None: raise ValueError("Cheque not found")
    if locked.status not in {"received","issued","returned","resubmitted"}: raise ValueError("Cheque cannot be replaced in its current status")
    if replacement.amount <= 0: raise ValueError("Replacement amount must be positive")
    new_cheque = Cheque(company_id=locked.company_id, partner_id=locked.partner_id, direction=locked.direction, cheque_number=replacement.cheque_number, bank_name=replacement.bank_name or locked.bank_name, account_number=replacement.account_number or locked.account_number, cheque_date=replacement.cheque_date or action_date, due_date=replacement.due_date or locked.due_date, amount=replacement.amount, currency=replacement.currency or locked.currency, status=locked.direction, original_cheque_id=locked.id, source_payment_id=locked.source_payment_id, notes=replacement.notes, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    db.add(new_cheque); db.flush()
    old=locked.status; locked.status="cancelled"; _record_event(db, locked, old, "cancelled", "replaced", action_date, user_id, replacement.cheque_number, replacement.notes)
    _record_event(db, new_cheque, None, new_cheque.status, "replacement_created", action_date, user_id, locked.cheque_number, replacement.notes)
    return new_cheque


def reconciliation_summary(db: Session, company_id: int):
    rows=db.execute(select(Cheque.status, func.count(Cheque.id), func.coalesce(func.sum(Cheque.amount),0)).where(Cheque.company_id==company_id).group_by(Cheque.status)).all()
    return [{"status":s,"count":int(n),"amount":a} for s,n,a in rows]
