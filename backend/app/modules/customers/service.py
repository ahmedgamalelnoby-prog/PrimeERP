from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .models import Customer
from .schemas import CustomerCreate, CustomerUpdate

class CustomerService:
    def list(self, db: Session, tenant_id: int, active_only: bool=False, search: str|None=None):
        stmt=select(Customer).where(Customer.tenant_id==tenant_id)
        if active_only: stmt=stmt.where(Customer.is_active.is_(True))
        if search: stmt=stmt.where(Customer.name.ilike(f"%{search}%"))
        return list(db.scalars(stmt.order_by(Customer.name, Customer.id)).all())
    def get(self, db: Session, tenant_id: int, customer_id: int):
        obj=db.scalar(select(Customer).where(Customer.id==customer_id, Customer.tenant_id==tenant_id))
        if obj is None: raise HTTPException(status_code=404, detail="Customer not found")
        return obj
    def create(self, db: Session, tenant_id: int, payload: CustomerCreate):
        obj=Customer(tenant_id=tenant_id, **payload.model_dump()); db.add(obj)
        try: db.commit()
        except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409, detail="Customer code already exists for this tenant") from exc
        db.refresh(obj); return obj
    def update(self, db: Session, tenant_id: int, customer_id: int, payload: CustomerUpdate):
        obj=self.get(db,tenant_id,customer_id)
        for k,v in payload.model_dump(exclude_unset=True).items(): setattr(obj,k,v)
        try: db.commit()
        except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409, detail="Customer code already exists for this tenant") from exc
        db.refresh(obj); return obj
customer_service=CustomerService()
