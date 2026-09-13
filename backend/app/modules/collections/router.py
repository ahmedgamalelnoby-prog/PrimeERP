from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.saas.entitlements import require_module
from app.modules.transactions.schemas import TransactionListResponse, TransactionResponse, TransactionReverseRequest
from app.modules.transactions.services.transaction_service import transaction_service


_COLLECTION_TYPES = ("collection", "customer_payment", "payment", "receipt")

router = APIRouter(
    prefix="/collections",
    tags=["Collections"],
    dependencies=[
        Depends(require_permission("transaction.access")),
        Depends(require_module("sales")),
    ],
)


@router.get("", response_model=TransactionListResponse)
def list_collections(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    company_id: Optional[int] = Query(default=None, gt=0),
    branch_id: Optional[int] = Query(default=None, gt=0),
    transaction_status: Optional[str] = Query(default=None, alias="status"),
    transaction_type: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None, max_length=150),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    types = (transaction_type,) if transaction_type else _COLLECTION_TYPES
    items = []
    for kind in types:
        if kind not in _COLLECTION_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported collection transaction type")
        result = transaction_service.list_transactions(
            db=db,
            current_user=current_user,
            page=1,
            page_size=200,
            company_id=company_id,
            branch_id=branch_id,
            transaction_type=kind,
            transaction_status=transaction_status,
            search=search,
        )
        items.extend(result["items"])

    items.sort(key=lambda item: (item.transaction_date, item.id), reverse=True)
    total = len(items)
    start = (page - 1) * page_size
    return {"items": items[start : start + page_size], "total": total, "page": page, "page_size": page_size}


@router.post(
    "/{transaction_number}/reverse",
    response_model=TransactionResponse,
    dependencies=[Depends(require_permission("transaction.reverse"))],
)
def reverse_collection(
    transaction_number: str,
    payload: TransactionReverseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    original = transaction_service.get_by_number(db=db, transaction_number=transaction_number, current_user=current_user)
    if original.transaction_type not in _COLLECTION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only collection/payment transactions can be reversed from Collections",
        )
    return transaction_service.reverse_transaction(
        db=db,
        transaction_number=transaction_number,
        reason=payload.reason,
        current_user=current_user,
    )
