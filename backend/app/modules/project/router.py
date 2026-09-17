from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.enterprise.models import Project
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.project.models import ProjectTask
from app.modules.saas.entitlements import require_module
from app.services.application_services import ApplicationServiceError, add_task_dependency, complete_task

router = APIRouter(prefix="/projects", tags=["Project"], dependencies=[Depends(require_module("project"))])


class DependencyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    predecessor_task_id: int
    successor_task_id: int


def _project(db: Session, user: User, project_id: int) -> Project:
    project = db.scalar(
        select(Project).join(Company, Company.id == Project.company_id).where(
            Project.id == project_id,
            Company.tenant_id == get_effective_tenant_id(user),
        )
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _error(exc: ApplicationServiceError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@router.get("/{project_id}/tasks")
def list_tasks(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _project(db, current_user, project_id)
    return list(db.scalars(select(ProjectTask).where(ProjectTask.project_id == project_id).order_by(ProjectTask.id)).all())


@router.post("/{project_id}/task-dependencies", status_code=201)
def create_dependency(project_id: int, payload: DependencyCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _project(db, current_user, project_id)
    try:
        add_task_dependency(db, project_id=project_id, **payload.model_dump())
        db.commit()
        return {"predecessor_task_id": payload.predecessor_task_id, "successor_task_id": payload.successor_task_id}
    except ApplicationServiceError as exc:
        db.rollback()
        raise _error(exc) from exc


@router.post("/{project_id}/tasks/{task_id}/complete")
def complete(project_id: int, task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _project(db, current_user, project_id)
    try:
        task = complete_task(db, task_id=task_id, project_id=project_id)
        db.commit()
        db.refresh(task)
        return task
    except ApplicationServiceError as exc:
        db.rollback()
        raise _error(exc) from exc
