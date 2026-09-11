from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.purchasing.suppliers.models import Supplier


class SupplierService:
    def list(self, db: Session, company_id: int, active_only: bool = True):
        stmt = select(Supplier).where(Supplier.company_id == company_id)
        if active_only:
            stmt = stmt.where(Supplier.is_active == 1)
        return list(db.scalars(stmt.order_by(Supplier.name)).all())

    def get(self, db: Session, company_id: int, supplier_id: int):
        return db.scalar(select(Supplier).where(Supplier.company_id == company_id, Supplier.id == supplier_id))

    def create(self, db: Session, payload):
        supplier = Supplier(**payload.model_dump())
        db.add(supplier)
        try:
            db.flush()
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("Supplier code already exists for this company") from exc
        return supplier

    def update(self, db: Session, company_id: int, supplier_id: int, payload):
        supplier = self.get(db, company_id, supplier_id)
        if supplier is None:
            raise ValueError("Supplier not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            if key == "is_active" and value is not None:
                value = 1 if value else 0
            setattr(supplier, key, value)
        db.flush()
        return supplier


supplier_service = SupplierService()
