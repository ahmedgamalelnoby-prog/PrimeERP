from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.transactions.schemas import (
    GeneratedNumberResponse,
    GenerateNumberRequest,
    NumberSequenceCreate,
    NumberSequenceResponse,
    NumberSequenceUpdate,
    TransactionActionRequest,
    TransactionCancelRequest,
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
    TransactionReverseRequest,
    TransactionUpdate,
)
from app.modules.transactions.services.numbering_service import numbering_service
from app.modules.transactions.services.transaction_service import transaction_service

router = APIRouter(
    dependencies=[Depends(require_permission("transaction.access"))],
)


def require_tenant_user(current_user: User) -> int:
    return get_effective_tenant_id(current_user)


@router.get("/number-sequences", response_model=list[NumberSequenceResponse])
def list_number_sequences(company_id: Optional[int] = Query(default=None, gt=0), branch_id: Optional[int] = Query(default=None, gt=0), is_active: Optional[bool] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return numbering_service.list_sequences(db=db, current_tenant_id=require_tenant_user(current_user), company_id=company_id, branch_id=branch_id, is_active=is_active)


@router.post("/number-sequences", response_model=NumberSequenceResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("transaction.write"))])
def create_number_sequence(payload: NumberSequenceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return numbering_service.create_sequence(db=db, payload=payload, current_tenant_id=require_tenant_user(current_user))


@router.post("/number-sequences/generate", response_model=GeneratedNumberResponse, dependencies=[Depends(require_permission("transaction.write"))])
def generate_next_number(payload: GenerateNumberRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = require_tenant_user(current_user)
    if payload.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access to another tenant is not allowed")
    return numbering_service.generate_next_number(db=db, tenant_id=tenant_id, company_id=payload.company_id, branch_id=payload.branch_id, sequence_key=payload.sequence_key)


@router.get("/number-sequences/{sequence_id}", response_model=NumberSequenceResponse)
def get_number_sequence(sequence_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return numbering_service.get_sequence(db=db, sequence_id=sequence_id, current_tenant_id=require_tenant_user(current_user))


@router.put("/number-sequences/{sequence_id}", response_model=NumberSequenceResponse, dependencies=[Depends(require_permission("transaction.write"))])
def update_number_sequence(sequence_id: int, payload: NumberSequenceUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return numbering_service.update_sequence(db=db, sequence_id=sequence_id, payload=payload, current_tenant_id=require_tenant_user(current_user))


@router.get("/", response_model=TransactionListResponse)
def list_transactions(page: int = Query(default=1, ge=1), page_size: int = Query(default=25, ge=1, le=200), company_id: Optional[int] = Query(default=None, gt=0), branch_id: Optional[int] = Query(default=None, gt=0), transaction_type: Optional[str] = None, transaction_status: Optional[str] = Query(default=None, alias="status"), search: Optional[str] = Query(default=None, max_length=150), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return transaction_service.list_transactions(db=db, current_user=current_user, page=page, page_size=page_size, company_id=company_id, branch_id=branch_id, transaction_type=transaction_type, transaction_status=transaction_status, search=search)


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("transaction.write"))])
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return transaction_service.create_transaction(db=db, payload=payload, current_user=current_user)


@router.get("/by-number/{transaction_number}", response_model=TransactionResponse)
def get_transaction_by_number(transaction_number: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return transaction_service.get_by_number(db=db, transaction_number=transaction_number, current_user=current_user)


@router.post("/by-number/{transaction_number}/cancel", response_model=TransactionResponse, dependencies=[Depends(require_permission("transaction.write"))])
def cancel_transaction(transaction_number: str, payload: TransactionCancelRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return transaction_service.cancel_transaction(db=db, transaction_number=transaction_number, reason=payload.reason, current_user=current_user)


@router.post("/by-number/{transaction_number}/reverse", response_model=TransactionResponse, dependencies=[Depends(require_permission("transaction.reverse"))])
def reverse_transaction(transaction_number: str, payload: TransactionReverseRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return transaction_service.reverse_transaction(db=db, transaction_number=transaction_number, reason=payload.reason, current_user=current_user)


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return transaction_service.get_by_id(db=db, transaction_id=transaction_id, current_user=current_user)


@router.put("/{transaction_id}", response_model=TransactionResponse, dependencies=[Depends(require_permission("transaction.write"))])
def update_transaction(transaction_id: int, payload: TransactionUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return transaction_service.update_transaction(db=db, transaction_id=transaction_id, payload=payload, current_user=current_user)


@router.post("/{transaction_id}/submit", response_model=TransactionResponse, dependencies=[Depends(require_permission("transaction.write"))])
def submit_transaction(transaction_id: int, payload: TransactionActionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return transaction_service.submit_transaction(db=db, transaction_id=transaction_id, current_user=current_user, reason=payload.reason)


@router.post("/{transaction_id}/approve", response_model=TransactionResponse, dependencies=[Depends(require_permission("transaction.post"))])
def approve_transaction(transaction_id: int, payload: TransactionActionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return transaction_service.approve_transaction(db=db, transaction_id=transaction_id, current_user=current_user, reason=payload.reason)


@router.post("/{transaction_id}/post", response_model=TransactionResponse, dependencies=[Depends(require_permission("transaction.post"))])
def post_transaction(transaction_id: int, payload: TransactionActionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return transaction_service.post_transaction(db=db, transaction_id=transaction_id, current_user=current_user, reason=payload.reason)
