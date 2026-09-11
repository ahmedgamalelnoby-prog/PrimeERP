from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.treasury.models import Cheque
from app.modules.treasury.schemas import ChequeAction, ChequeCreate, ChequeEventResponse, ChequeResponse
from app.modules.treasury.service import create_cheque, events, list_cheques, resubmit_returned_cheque, transition_cheque, withdraw_cheque

router = APIRouter(prefix="/treasury", tags=["Treasury"], dependencies=[Depends(require_permission("treasury.access"))])


def _company(db: Session, company_id: int, user: User):
    if user.tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == user.tenant_id))
    if company is None:
        raise HTTPException(403, "Company is outside the current tenant")
    return company


def _get_cheque(db: Session, company_id: int, cheque_id: int):
    cheque = db.scalar(select(Cheque).where(Cheque.id == cheque_id, Cheque.company_id == company_id))
    if cheque is None:
        raise HTTPException(404, "Cheque not found")
    return cheque


@router.post("/cheques", response_model=ChequeResponse, status_code=201, dependencies=[Depends(require_permission("treasury.write"))])
def create(payload: ChequeCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, payload.company_id, current_user)
    try:
        obj = create_cheque(db, payload, current_user.id)
        db.commit(); db.refresh(obj)
        return obj
    except ValueError as exc:
        db.rollback(); raise HTTPException(400, str(exc)) from exc


@router.get("/cheques", response_model=list[ChequeResponse])
def list_all(company_id: int = Query(..., gt=0), status: str | None = None, direction: str | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    return list_cheques(db, company_id, status, direction)


@router.get("/cheques/withdrawable", response_model=list[ChequeResponse])
def withdrawable(company_id: int = Query(..., gt=0), as_of: date | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    as_of = as_of or date.today()
    return [c for c in list_cheques(db, company_id, direction="received") if c.status not in {"withdrawn", "cancelled", "reversed"} and (c.cheque_date >= as_of or c.due_date >= as_of)]


@router.get("/cheques/{cheque_id}/events", response_model=list[ChequeEventResponse])
def history(cheque_id: int, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user); _get_cheque(db, company_id, cheque_id)
    return events(db, company_id, cheque_id)


@router.post("/cheques/{cheque_id}/deposit", response_model=ChequeResponse, dependencies=[Depends(require_permission("treasury.write"))])
def deposit(cheque_id: int, payload: ChequeAction, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, payload.company_id, current_user); cheque = _get_cheque(db, payload.company_id, cheque_id)
    try: obj = transition_cheque(db, cheque, "deposited", payload.event_date or date.today(), current_user.id, "deposited", payload.reference, payload.notes); db.commit(); db.refresh(obj); return obj
    except ValueError as exc: db.rollback(); raise HTTPException(400, str(exc)) from exc


@router.post("/cheques/{cheque_id}/under-collection", response_model=ChequeResponse, dependencies=[Depends(require_permission("treasury.write"))])
def under_collection(cheque_id: int, payload: ChequeAction, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, payload.company_id, current_user); cheque = _get_cheque(db, payload.company_id, cheque_id)
    try: obj = transition_cheque(db, cheque, "under_collection", payload.event_date or date.today(), current_user.id, "under_collection", payload.reference, payload.notes); db.commit(); db.refresh(obj); return obj
    except ValueError as exc: db.rollback(); raise HTTPException(400, str(exc)) from exc


@router.post("/cheques/{cheque_id}/collect", response_model=ChequeResponse, dependencies=[Depends(require_permission("treasury.post"))])
def collect(cheque_id: int, payload: ChequeAction, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, payload.company_id, current_user); cheque = _get_cheque(db, payload.company_id, cheque_id)
    try: obj = transition_cheque(db, cheque, "collected", payload.event_date or date.today(), current_user.id, "collected", payload.reference, payload.notes); db.commit(); db.refresh(obj); return obj
    except ValueError as exc: db.rollback(); raise HTTPException(400, str(exc)) from exc


@router.post("/cheques/{cheque_id}/return", response_model=ChequeResponse, dependencies=[Depends(require_permission("treasury.post"))])
def returned(cheque_id: int, payload: ChequeAction, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, payload.company_id, current_user); cheque = _get_cheque(db, payload.company_id, cheque_id)
    try: obj = transition_cheque(db, cheque, "returned", payload.event_date or date.today(), current_user.id, "returned", payload.reference, payload.notes); db.commit(); db.refresh(obj); return obj
    except ValueError as exc: db.rollback(); raise HTTPException(400, str(exc)) from exc


@router.post("/cheques/{cheque_id}/resubmit", response_model=ChequeResponse, dependencies=[Depends(require_permission("treasury.write"))])
def resubmit(cheque_id: int, payload: ChequeAction, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, payload.company_id, current_user); cheque = _get_cheque(db, payload.company_id, cheque_id)
    try: obj = resubmit_returned_cheque(db, cheque, payload.event_date or date.today(), current_user.id, payload.reference, payload.notes); db.commit(); db.refresh(obj); return obj
    except ValueError as exc: db.rollback(); raise HTTPException(400, str(exc)) from exc


@router.post("/cheques/{cheque_id}/withdraw", response_model=ChequeResponse, dependencies=[Depends(require_permission("treasury.write"))])
def withdraw(cheque_id: int, payload: ChequeAction, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, payload.company_id, current_user); cheque = _get_cheque(db, payload.company_id, cheque_id)
    try: obj = withdraw_cheque(db, cheque, payload.event_date or date.today(), current_user.id, payload.reference, payload.notes); db.commit(); db.refresh(obj); return obj
    except ValueError as exc: db.rollback(); raise HTTPException(400, str(exc)) from exc
