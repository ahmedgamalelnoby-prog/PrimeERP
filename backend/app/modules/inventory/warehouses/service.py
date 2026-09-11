from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.branches.models import Branch
from app.modules.companies.models import Company
from app.modules.inventory.warehouses.models import InventoryWarehouse
from app.modules.inventory.warehouses.schemas import WarehouseCreate, WarehouseUpdate


class WarehouseService:
    def list(self, db: Session, *, tenant_id: int, company_id: int, branch_id: int | None = None):
        stmt = select(InventoryWarehouse).where(
            InventoryWarehouse.tenant_id == tenant_id,
            InventoryWarehouse.company_id == company_id,
        )
        if branch_id is not None:
            stmt = stmt.where(
                (InventoryWarehouse.branch_id == branch_id) | InventoryWarehouse.is_central.is_(True)
            )
        return db.scalars(stmt.order_by(InventoryWarehouse.is_central.desc(), InventoryWarehouse.code)).all()

    def create(self, db: Session, payload: WarehouseCreate):
        company = db.scalar(select(Company).where(Company.id == payload.company_id, Company.tenant_id == payload.tenant_id))
        if company is None:
            raise ValueError("Company does not belong to tenant")

        if payload.is_central:
            if payload.branch_id is not None:
                raise ValueError("A central warehouse cannot belong to a branch")
            existing = db.scalar(select(InventoryWarehouse).where(
                InventoryWarehouse.company_id == payload.company_id,
                InventoryWarehouse.is_central.is_(True),
                InventoryWarehouse.is_active.is_(True),
            ))
            if existing:
                raise ValueError("An active central warehouse already exists for this company")
        else:
            if payload.branch_id is None:
                raise ValueError("A branch warehouse requires a branch")
            branch = db.scalar(select(Branch).where(
                Branch.id == payload.branch_id,
                Branch.company_id == payload.company_id,
                Branch.tenant_id == payload.tenant_id,
            ))
            if branch is None:
                raise ValueError("Branch does not belong to company")

        warehouse = InventoryWarehouse(**payload.model_dump())
        db.add(warehouse)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("Warehouse code already exists for this company") from exc
        db.refresh(warehouse)
        return warehouse

    def update(self, db: Session, *, tenant_id: int, warehouse_id: int, payload: WarehouseUpdate):
        warehouse = db.scalar(select(InventoryWarehouse).where(
            InventoryWarehouse.id == warehouse_id,
            InventoryWarehouse.tenant_id == tenant_id,
        ))
        if warehouse is None:
            raise ValueError("Warehouse not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(warehouse, key, value)
        db.commit()
        db.refresh(warehouse)
        return warehouse

    def get_central(self, db: Session, *, tenant_id: int, company_id: int):
        return db.scalar(select(InventoryWarehouse).where(
            InventoryWarehouse.tenant_id == tenant_id,
            InventoryWarehouse.company_id == company_id,
            InventoryWarehouse.is_central.is_(True),
            InventoryWarehouse.is_active.is_(True),
        ))


warehouse_service = WarehouseService()
