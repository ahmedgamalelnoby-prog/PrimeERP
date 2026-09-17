from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.saas.entitlements import require_module
from app.modules.helpdesk.models import HelpdeskStage, HelpdeskTeam, HelpdeskTicket
from app.services.application_services import (
    ApplicationServiceError,
    add_helpdesk_follower,
    assign_helpdesk_ticket,
    create_helpdesk_ticket,
    transition_helpdesk_ticket,
)

router = APIRouter(prefix="/helpdesk", tags=["Helpdesk"], dependencies=[Depends(require_module("helpdesk"))])


class TicketCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company_id: int
    team_id: int
    stage_id: int
    ticket_no: str
    subject: str
    customer_ref: str | None = None
    assignee_ref: str | None = None
    sla_due_at: datetime | None = None


class StageTransition(BaseModel):
    stage_id: int


class Assignment(BaseModel):
    member_ref: str


class Follower(BaseModel):
    follower_ref: str


def _company(db: Session, user: User, company_id: int) -> Company:
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == get_effective_tenant_id(user)))
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


def _error(exc: ApplicationServiceError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@router.get("/teams")
def list_teams(company_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company(db, current_user, company_id)
    return list(db.scalars(select(HelpdeskTeam).where(HelpdeskTeam.company_id == company_id, HelpdeskTeam.active.is_(True)).order_by(HelpdeskTeam.name)).all())


@router.get("/teams/{team_id}/stages")
def list_stages(team_id: int, company_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company(db, current_user, company_id)
    team = db.scalar(select(HelpdeskTeam).where(HelpdeskTeam.id == team_id, HelpdeskTeam.company_id == company_id))
    if team is None:
        raise HTTPException(status_code=404, detail="Helpdesk team not found")
    return list(db.scalars(select(HelpdeskStage).where(HelpdeskStage.team_id == team_id).order_by(HelpdeskStage.sequence, HelpdeskStage.id)).all())


@router.post("/tickets", status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company(db, current_user, payload.company_id)
    try:
        ticket = create_helpdesk_ticket(db, **payload.model_dump())
        db.commit()
        db.refresh(ticket)
        return ticket
    except ApplicationServiceError as exc:
        db.rollback()
        raise _error(exc) from exc


@router.post("/tickets/{ticket_id}/transition")
def transition_ticket(ticket_id: int, payload: StageTransition, company_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company(db, current_user, company_id)
    try:
        ticket = transition_helpdesk_ticket(db, ticket_id=ticket_id, company_id=company_id, stage_id=payload.stage_id)
        db.commit()
        db.refresh(ticket)
        return ticket
    except ApplicationServiceError as exc:
        db.rollback()
        raise _error(exc) from exc


@router.post("/tickets/{ticket_id}/assign")
def assign_ticket(ticket_id: int, payload: Assignment, company_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company(db, current_user, company_id)
    try:
        ticket = assign_helpdesk_ticket(db, ticket_id=ticket_id, company_id=company_id, member_ref=payload.member_ref)
        db.commit()
        db.refresh(ticket)
        return ticket
    except ApplicationServiceError as exc:
        db.rollback()
        raise _error(exc) from exc


@router.post("/tickets/{ticket_id}/followers", status_code=status.HTTP_204_NO_CONTENT)
def add_follower(ticket_id: int, payload: Follower, company_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company(db, current_user, company_id)
    try:
        add_helpdesk_follower(db, ticket_id=ticket_id, company_id=company_id, follower_ref=payload.follower_ref)
        db.commit()
    except ApplicationServiceError as exc:
        db.rollback()
        raise _error(exc) from exc
