from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.uom.models import UnitOfMeasure

router = APIRouter(prefix="/inventory/uom", tags=["Inventory UOM"])


class UomCreate(BaseModel):
    company_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=50)
    factor_to_base: float = Field(gt=0)
    is_base: bool = False


class UomResponse(UomCreate):
    id: int
    is_active: bool

    model_config = {"from_attributes": True}


@router.post("", response_model=UomResponse, status_code=201)
def create_uom(payload: UomCreate, db: Session = Depends(get_db)):
    if payload.is_base:
        db.query(UnitOfMeasure).filter(
            UnitOfMeasure.company_id == payload.company_id,
            UnitOfMeasure.category == payload.category,
        ).update({"is_base": False}, synchronize_session=False)
    obj = UnitOfMeasure(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("", response_model=list[UomResponse])
def list_uom(
    company_id: int = Query(..., gt=0),
    category: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(UnitOfMeasure).filter(
        UnitOfMeasure.company_id == company_id,
        UnitOfMeasure.is_active.is_(True),
    )
    if category:
        q = q.filter(UnitOfMeasure.category == category)
    return q.order_by(UnitOfMeasure.category, UnitOfMeasure.code).all()
