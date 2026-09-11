from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.session import get_db
from .models import UnitOfMeasure
from .schemas import UOMCreate, UOMResponse

router = APIRouter(prefix='/uom', tags=['Units of Measure'])

@router.post('', response_model=UOMResponse, status_code=201)
def create_uom(payload: UOMCreate, db: Session = Depends(get_db)):
    if db.scalar(select(UnitOfMeasure).where(UnitOfMeasure.company_id==payload.company_id,UnitOfMeasure.code==payload.code)):
        raise HTTPException(409,'UOM code already exists')
    if payload.is_base and db.scalar(select(UnitOfMeasure).where(UnitOfMeasure.company_id==payload.company_id,UnitOfMeasure.category==payload.category,UnitOfMeasure.is_base.is_(True))):
        raise HTTPException(409,'A base UOM already exists for this category')
    obj=UnitOfMeasure(**payload.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj

@router.get('', response_model=list[UOMResponse])
def list_uom(company_id:int=Query(...,gt=0),category:str|None=None,db:Session=Depends(get_db)):
    q=select(UnitOfMeasure).where(UnitOfMeasure.company_id==company_id,UnitOfMeasure.is_active.is_(True))
    if category: q=q.where(UnitOfMeasure.category==category)
    return list(db.scalars(q.order_by(UnitOfMeasure.category,UnitOfMeasure.code)).all())

@router.get('/convert')
def convert(company_id:int, quantity:Decimal, from_uom_id:int, to_uom_id:int, db:Session=Depends(get_db)):
    rows=db.scalars(select(UnitOfMeasure).where(UnitOfMeasure.id.in_([from_uom_id,to_uom_id]),UnitOfMeasure.company_id==company_id,UnitOfMeasure.is_active.is_(True))).all()
    by_id={x.id:x for x in rows}
    if len(by_id)!=2: raise HTTPException(404,'UOM not found')
    if by_id[from_uom_id].category != by_id[to_uom_id].category: raise HTTPException(400,'UOM categories do not match')
    return {'quantity':quantity,'from_uom_id':from_uom_id,'to_uom_id':to_uom_id,'converted_quantity':quantity*by_id[from_uom_id].factor_to_base/by_id[to_uom_id].factor_to_base}
