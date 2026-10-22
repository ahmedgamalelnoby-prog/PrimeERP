from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.audit.service import record_audit_event
from app.modules.companies.models import Company
from app.modules.company_settings.consumers.approvals import approval_mode
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.operations.approvals.models import ApprovalRequest, ApprovalStep
from app.modules.operations.approvals.schemas import ApprovalDecision, ApprovalRequestCreate, ApprovalRequestView
from app.modules.operations.approvals.service import create_approval_request, decide_approval

router = APIRouter(prefix="/approvals", tags=["Approvals"])


def _tenant_id(user: User) -> int:
    tenant_id = get_effective_tenant_id(user)
    if tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    return tenant_id


def _company(db: Session, company_id: int, tenant_id: int) -> Company:
    company = db.scalar(select(Company).where(
        Company.id == company_id,
        Company.tenant_id == tenant_id,
        Company.is_active.is_(True),
    ))
    if company is None:
        raise HTTPException(404, "Active company not found in current tenant")
    return company


def _audit(db: Session, *, action: str, request: ApprovalRequest, user: User) -> None:
    record_audit_event(
        db, action=action, entity_type="approval_request", entity_id=request.id,
        user_id=user.id, tenant_id=request.tenant_id, company_id=request.company_id,
        metadata={"status": request.status, "mode": request.mode, "entity_type": request.entity_type},
    )


@router.get(
    "/requests",
    response_model=list[ApprovalRequestView],
    dependencies=[Depends(require_permission("enterprise.access"))],
)
def list_approval_requests(
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tenant_id = _tenant_id(user)
    _company(db, company_id, tenant_id)
    return list(db.scalars(
        select(ApprovalRequest)
        .options(selectinload(ApprovalRequest.steps))
        .where(ApprovalRequest.tenant_id == tenant_id, ApprovalRequest.company_id == company_id)
        .order_by(ApprovalRequest.created_at.desc(), ApprovalRequest.id.desc())
    ).all())


@router.post(
    "/requests",
    response_model=ApprovalRequestView,
    status_code=201,
    dependencies=[Depends(require_permission("enterprise.write"))],
)
def submit_approval_request(
    payload: ApprovalRequestCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tenant_id = _tenant_id(user)
    _company(db, payload.company_id, tenant_id)
    if user.id in payload.approver_ids:
        raise HTTPException(422, "Requester cannot approve their own request")
    approvers = list(db.scalars(select(User).where(
        User.id.in_(payload.approver_ids),
        User.tenant_id == tenant_id,
        User.is_active.is_(True),
        User.is_deleted.is_(False),
    )).all())
    if {item.id for item in approvers} != set(payload.approver_ids):
        raise HTTPException(422, "Every approver must be an active user in the current tenant")
    try:
        mode = approval_mode(db, payload.company_id)
        request = create_approval_request(
            db, tenant_id=tenant_id, company_id=payload.company_id,
            requester_id=user.id, entity_type=payload.entity_type,
            entity_id=payload.entity_id, title=payload.title,
            mode=mode, approver_ids=payload.approver_ids,
        )
        _audit(db, action="approval.request_submitted", request=request, user=user)
        db.commit()
        return db.scalar(select(ApprovalRequest).options(selectinload(ApprovalRequest.steps)).where(
            ApprovalRequest.id == request.id, ApprovalRequest.tenant_id == tenant_id
        ))
    except ValueError as exc:
        db.rollback()
        raise HTTPException(422, str(exc)) from exc
    except Exception:
        db.rollback()
        raise


@router.post(
    "/requests/{request_id}/decision",
    response_model=ApprovalRequestView,
    dependencies=[Depends(require_permission("enterprise.write"))],
)
def decide_approval_request(
    request_id: int,
    payload: ApprovalDecision,
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tenant_id = _tenant_id(user)
    _company(db, company_id, tenant_id)
    request = db.scalar(select(ApprovalRequest).options(selectinload(ApprovalRequest.steps)).where(
        ApprovalRequest.id == request_id,
        ApprovalRequest.tenant_id == tenant_id,
        ApprovalRequest.company_id == company_id,
    ).with_for_update())
    if request is None:
        raise HTTPException(404, "Approval request not found")
    try:
        decide_approval(
            db, request=request, actor_user_id=user.id,
            decision=payload.decision, reason=payload.reason,
        )
        _audit(db, action="approval.request_decided", request=request, user=user)
        db.commit()
        return db.scalar(select(ApprovalRequest).options(selectinload(ApprovalRequest.steps)).where(
            ApprovalRequest.id == request.id, ApprovalRequest.tenant_id == tenant_id
        ))
    except PermissionError as exc:
        db.rollback()
        raise HTTPException(403, str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc
    except Exception:
        db.rollback()
        raise
