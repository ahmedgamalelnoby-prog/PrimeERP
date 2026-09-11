from sqlalchemy.orm import Session

from app.modules.inventory.warehouses.models import InventoryWarehouse


class WarehouseService:
    def list(self, db: Session, *, company_id: int, branch_id: int | None = None, include_central: bool = True):
        query = db.query(InventoryWarehouse).filter(
            InventoryWarehouse.company_id == company_id,
            InventoryWarehouse.is_active.is_(True),
        )
        if branch_id is not None:
            if include_central:
                query = query.filter(
                    (InventoryWarehouse.branch_id == branch_id) | InventoryWarehouse.is_central.is_(True)
                )
            else:
                query = query.filter(InventoryWarehouse.branch_id == branch_id)
        return query.order_by(InventoryWarehouse.is_central.desc(), InventoryWarehouse.code).all()

    def get(self, db: Session, *, company_id: int, warehouse_id: int):
        return db.query(InventoryWarehouse).filter(
            InventoryWarehouse.id == warehouse_id,
            InventoryWarehouse.company_id == company_id,
        ).first()

    def create(
        self,
        db: Session,
        *,
        tenant_id: int,
        company_id: int,
        branch_id: int | None,
        code: str,
        name: str,
        description: str | None = None,
        is_central: bool = False,
    ):
        if is_central and branch_id is not None:
            raise ValueError("A central warehouse cannot belong to a branch")
        if not is_central and branch_id is None:
            raise ValueError("A branch warehouse requires a branch")
        if is_central and db.query(InventoryWarehouse).filter(
            InventoryWarehouse.company_id == company_id,
            InventoryWarehouse.is_central.is_(True),
            InventoryWarehouse.is_active.is_(True),
        ).first():
            raise ValueError("Company already has an active central warehouse")

        warehouse = InventoryWarehouse(
            tenant_id=tenant_id,
            company_id=company_id,
            branch_id=branch_id,
            code=code.strip(),
            name=name.strip(),
            description=description,
            is_central=is_central,
        )
        db.add(warehouse)
        db.flush()
        return warehouse


warehouse_service = WarehouseService()
