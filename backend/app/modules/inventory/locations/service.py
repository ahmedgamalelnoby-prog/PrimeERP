from sqlalchemy.orm import Session

from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.locations.repository import location_repository
from app.modules.inventory.warehouses.models import InventoryWarehouse


VALID_TYPES = {"storage", "receiving", "shipping", "quarantine", "damaged", "transit", "virtual"}


class LocationService:
    def list(self, db: Session, *, company_id: int, warehouse_id: int):
        warehouse = db.query(InventoryWarehouse).filter(
            InventoryWarehouse.id == warehouse_id,
            InventoryWarehouse.company_id == company_id,
        ).first()
        if warehouse is None:
            raise ValueError("Warehouse not found")
        return location_repository.list(db, company_id=company_id, warehouse_id=warehouse_id)

    def create(self, db: Session, *, payload):
        warehouse = db.query(InventoryWarehouse).filter(
            InventoryWarehouse.id == payload.warehouse_id,
            InventoryWarehouse.company_id == payload.company_id,
            InventoryWarehouse.is_active.is_(True),
        ).first()
        if warehouse is None:
            raise ValueError("Warehouse not found for company")
        if payload.location_type not in VALID_TYPES:
            raise ValueError("Invalid location type")
        if payload.parent_id is not None:
            parent = location_repository.get(db, company_id=payload.company_id, location_id=payload.parent_id)
            if parent is None or parent.warehouse_id != payload.warehouse_id:
                raise ValueError("Parent location must belong to the same warehouse")
        if payload.is_virtual and payload.location_type != "virtual":
            raise ValueError("Virtual locations must use location_type=virtual")

        location = InventoryLocation(
            company_id=payload.company_id,
            warehouse_id=payload.warehouse_id,
            parent_id=payload.parent_id,
            code=payload.code.strip(),
            name=payload.name.strip(),
            location_type=payload.location_type,
            is_virtual=payload.is_virtual,
            description=payload.description,
        )
        db.add(location)
        db.flush()
        return location

    def update(self, db: Session, *, company_id: int, location_id: int, payload):
        location = location_repository.get(db, company_id=company_id, location_id=location_id)
        if location is None:
            raise ValueError("Location not found")
        if payload.location_type is not None and payload.location_type not in VALID_TYPES:
            raise ValueError("Invalid location type")
        if payload.name is not None:
            location.name = payload.name.strip()
        if payload.location_type is not None:
            location.location_type = payload.location_type
        if payload.is_virtual is not None:
            location.is_virtual = payload.is_virtual
        if payload.is_active is not None:
            location.is_active = payload.is_active
        if payload.description is not None:
            location.description = payload.description
        db.flush()
        return location


location_service = LocationService()
