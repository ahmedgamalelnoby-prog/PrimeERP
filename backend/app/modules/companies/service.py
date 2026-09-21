from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .models import Company
from .schemas import CompanyCreate, CompanyUpdate

class CompanyService:
    def list(self, db: Session, tenant_id: int, active_only: bool = False):
        stmt = select(Company).where(Company.tenant_id == tenant_id)
        if active_only: stmt = stmt.where(Company.is_active.is_(True))
        return list(db.scalars(stmt.order_by(Company.name, Company.id)).all())
    def get(self, db: Session, tenant_id: int, company_id: int):
        obj = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == tenant_id))
        if obj is None: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        return obj
    def create(self, db: Session, tenant_id: int, payload: CompanyCreate):
        obj = Company(tenant_id=tenant_id, **payload.model_dump()); db.add(obj)
        try: db.commit()
        except IntegrityError as exc:
            db.rollback(); raise HTTPException(status_code=409, detail="Company code already exists for this tenant") from exc
        db.refresh(obj); return obj
    def update(self, db: Session, tenant_id: int, company_id: int, payload: CompanyUpdate):
        obj = self.get(db, tenant_id, company_id)
        for key, value in payload.model_dump(exclude_unset=True).items(): setattr(obj, key, value)
        try: db.commit()
        except IntegrityError as exc:
            db.rollback(); raise HTTPException(status_code=409, detail="Company code already exists for this tenant") from exc
        db.refresh(obj); return obj

company_service = CompanyService()
