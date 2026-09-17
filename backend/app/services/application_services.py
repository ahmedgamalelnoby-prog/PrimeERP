from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.documents.models import Document, DocumentRequest, DocumentShare, DocumentVersion
from app.modules.helpdesk.models import HelpdeskFollower, HelpdeskStage, HelpdeskTeam, HelpdeskTeamMember, HelpdeskTicket
from app.modules.project.models import ProjectTask, ProjectTaskDependency


class ApplicationServiceError(ValueError):
    pass


def create_helpdesk_ticket(db: Session, *, company_id: int, team_id: int, stage_id: int,
                            ticket_no: str, subject: str, customer_ref: str | None = None,
                            assignee_ref: str | None = None, sla_due_at=None) -> HelpdeskTicket:
    team = db.scalar(select(HelpdeskTeam).where(HelpdeskTeam.id == team_id, HelpdeskTeam.company_id == company_id))
    stage = db.scalar(select(HelpdeskStage).where(HelpdeskStage.id == stage_id, HelpdeskStage.team_id == team_id))
    if not team or not stage:
        raise ApplicationServiceError("Team and stage must belong to the same company/team")
    if assignee_ref and not db.scalar(select(HelpdeskTeamMember).where(
        HelpdeskTeamMember.team_id == team_id,
        HelpdeskTeamMember.member_ref == assignee_ref,
        HelpdeskTeamMember.active.is_(True),
    )):
        raise ApplicationServiceError("Assignee is not an active member of the helpdesk team")
    ticket = HelpdeskTicket(company_id=company_id, team_id=team_id, stage_id=stage_id,
                            ticket_no=ticket_no, subject=subject, customer_ref=customer_ref,
                            assignee_ref=assignee_ref, sla_due_at=sla_due_at)
    db.add(ticket)
    db.flush()
    return ticket


def transition_helpdesk_ticket(db: Session, *, ticket_id: int, company_id: int, stage_id: int) -> HelpdeskTicket:
    ticket = db.scalar(select(HelpdeskTicket).where(HelpdeskTicket.id == ticket_id, HelpdeskTicket.company_id == company_id))
    stage = db.scalar(select(HelpdeskStage).where(HelpdeskStage.id == stage_id))
    if not ticket or not stage or stage.team_id != ticket.team_id:
        raise ApplicationServiceError("Ticket and stage must belong to the same company/team")
    ticket.stage_id = stage.id
    ticket.status = "closed" if stage.is_closed else "open"
    ticket.closed_at = datetime.now(timezone.utc) if stage.is_closed else None
    ticket.updated_at = datetime.now(timezone.utc)
    db.flush()
    return ticket


def assign_helpdesk_ticket(db: Session, *, ticket_id: int, company_id: int, member_ref: str) -> HelpdeskTicket:
    ticket = db.scalar(select(HelpdeskTicket).where(HelpdeskTicket.id == ticket_id, HelpdeskTicket.company_id == company_id))
    if not ticket:
        raise ApplicationServiceError("Ticket not found")
    if not db.scalar(select(HelpdeskTeamMember).where(
        HelpdeskTeamMember.team_id == ticket.team_id,
        HelpdeskTeamMember.member_ref == member_ref,
        HelpdeskTeamMember.active.is_(True),
    )):
        raise ApplicationServiceError("Assignee is not an active member of the helpdesk team")
    ticket.assignee_ref = member_ref
    ticket.updated_at = datetime.now(timezone.utc)
    db.flush()
    return ticket


def add_helpdesk_follower(db: Session, *, ticket_id: int, company_id: int, follower_ref: str) -> None:
    ticket = db.scalar(select(HelpdeskTicket).where(HelpdeskTicket.id == ticket_id, HelpdeskTicket.company_id == company_id))
    if not ticket:
        raise ApplicationServiceError("Ticket not found")
    db.merge(HelpdeskFollower(ticket_id=ticket_id, follower_ref=follower_ref))


def add_task_dependency(db: Session, *, predecessor_id: int, successor_id: int, project_id: int) -> None:
    if predecessor_id == successor_id:
        raise ApplicationServiceError("A task cannot depend on itself")
    predecessor = db.scalar(select(ProjectTask).where(ProjectTask.id == predecessor_id, ProjectTask.project_id == project_id))
    successor = db.scalar(select(ProjectTask).where(ProjectTask.id == successor_id, ProjectTask.project_id == project_id))
    if not predecessor or not successor:
        raise ApplicationServiceError("Dependency tasks must belong to the same project")
    stack = [successor_id]
    seen: set[int] = set()
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        if current == predecessor_id:
            raise ApplicationServiceError("Task dependency would create a cycle")
        rows = db.execute(select(ProjectTaskDependency.successor_task_id).where(
            ProjectTaskDependency.predecessor_task_id == current)).scalars().all()
        stack.extend(rows)
    db.add(ProjectTaskDependency(predecessor_task_id=predecessor_id, successor_task_id=successor_id))


def complete_task(db: Session, *, task_id: int, project_id: int) -> ProjectTask:
    task = db.scalar(select(ProjectTask).where(ProjectTask.id == task_id, ProjectTask.project_id == project_id))
    if not task:
        raise ApplicationServiceError("Task not found")
    blockers = db.execute(select(ProjectTask).join(
        ProjectTaskDependency, ProjectTaskDependency.predecessor_task_id == ProjectTask.id
    ).where(ProjectTaskDependency.successor_task_id == task_id, ProjectTask.status != "done")).scalars().all()
    if blockers:
        raise ApplicationServiceError("Task cannot be completed while predecessor tasks are not done")
    task.status = "done"
    task.completed_at = datetime.now(timezone.utc)
    return task


def create_document_version(db: Session, *, document_id: int, storage_uri: str,
                            created_by_ref: str | None = None, checksum: str | None = None) -> DocumentVersion:
    document = db.get(Document, document_id)
    if not document or document.status != "active":
        raise ApplicationServiceError("Document is not active")
    next_version = document.version_no + 1
    version = DocumentVersion(document_id=document_id, version_no=next_version,
                              storage_uri=storage_uri, created_by_ref=created_by_ref, checksum=checksum)
    document.version_no = next_version
    document.storage_uri = storage_uri
    document.updated_at = datetime.now(timezone.utc)
    db.add(version)
    db.flush()
    return version


def share_document(db: Session, *, document_id: int, grantee_ref: str, role: str,
                   expires_at=None) -> DocumentShare:
    if role not in {"viewer", "editor"}:
        raise ApplicationServiceError("Document role must be viewer or editor")
    document = db.get(Document, document_id)
    if not document or document.status != "active":
        raise ApplicationServiceError("Document is not active")
    share = DocumentShare(document_id=document_id, grantee_ref=grantee_ref, role=role, expires_at=expires_at, active=True)
    db.merge(share)
    db.flush()
    return share


def request_document(db: Session, *, company_id: int, document_name: str,
                     requested_from_ref: str, requested_by_ref: str, due_at=None,
                     message: str | None = None) -> DocumentRequest:
    request = DocumentRequest(company_id=company_id, document_name=document_name,
                              requested_from_ref=requested_from_ref, requested_by_ref=requested_by_ref,
                              due_at=due_at, message=message)
    db.add(request)
    db.flush()
    return request


def trash_document(db: Session, *, document_id: int) -> Document:
    document = db.get(Document, document_id)
    if not document:
        raise ApplicationServiceError("Document not found")
    document.status = "trashed"
    document.updated_at = datetime.now(timezone.utc)
    db.flush()
    return document
