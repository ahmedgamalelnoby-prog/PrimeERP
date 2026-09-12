from typing import List

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.platform.plans.schemas import PlanCreate, PlanResponse, PlanUpdate
from app.modules.platform.plans.service import PlanService


router = APIRouter(
    prefix="/plans",
    tags=["Platform Plans"],
)


def require_platform_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_platform_admin:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Platform administrator access required")
    return current_user


@router.get(
    "/",
    response_model=List[PlanResponse],
)
def get_plans(db: Session = Depends(get_db)):
    service = PlanService(db)
    return service.get_all_plans()


@router.get(
    "/{plan_id}",
    response_model=PlanResponse,
)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    service = PlanService(db)
    return service.get_plan(plan_id)


@router.post(
    "/",
    response_model=PlanResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_platform_admin)],
)
def create_plan(schema: PlanCreate, db: Session = Depends(get_db)):
    service = PlanService(db)
    return service.create_plan(schema)


@router.put(
    "/{plan_id}",
    response_model=PlanResponse,
    dependencies=[Depends(require_platform_admin)],
)
def update_plan(plan_id: int, schema: PlanUpdate, db: Session = Depends(get_db)):
    service = PlanService(db)
    return service.update_plan(plan_id=plan_id, schema=schema)


@router.delete(
    "/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_platform_admin)],
)
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    service = PlanService(db)
    service.delete_plan(plan_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
