from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.modules.companies.models import Company
from .models import Branch
from .schemas import BranchCreate, BranchUpdate
class BranchService:
    def _company(self, db, tenant_id, company_id):
        obj=db.scalar(select(Company).where(Company.id==company_id, Company.tenant_id==tenant_id))
        if obj is None: raise HTTPException(status_code=404, detail="Company not found")
        return obj
    def list(self, db, tenant_id, company_id=None):
        stmt=select(Branch).where(Branch.tenant_id==tenant_id)
        if company_id is not None: stmt=stmt.where(Branch.company_id==company_id)
        return list(db.scalars(stmt.order_by(Branch.name, Branch.id)).all())
    def get(self, db, tenant_id, branch_id):
        obj=db.scalar(select(Branch).where(Branch.id==branch_id, Branch.tenant_id==tenant_id))
        if obj is None: raise HTTPException(status_code=404, detail="Branch not found")
        return obj
    def create(self, db, tenant_id, payload):
        self._company(db, tenant_id, payload.company_id); obj=Branch(tenant_id=tenant_id, **payload.model_dump()); db.add(obj)
        try: db.commit()
        except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409, detail="Branch code already exists for this company") from exc
        db.refresh(obj); return obj
    def update(self, db, tenant_id, branch_id, payload):
        obj=self.get(db, tenant_id, branch_id); data=payload.model_dump(exclude_unset=True)
        if "company_id" in data: self._company(db, tenant_id, data["company_id"])
        for key,value in data.items(): setattr(obj,key,value)
        try: db.commit()
        except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409, detail="Branch code already exists for this company") from exc
        db.refresh(obj); return obj
branch_service=BranchService()
