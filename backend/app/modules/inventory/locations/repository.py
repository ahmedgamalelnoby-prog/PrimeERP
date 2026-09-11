from sqlalchemy.orm import Session

from app.modules.inventory.locations.models import InventoryLocation


class LocationRepository:
    def list(self, db: Session, *, company_id: int, warehouse_id: int):
        return db.query(InventoryLocation).filter(
            InventoryLocation.company_id == company_id,
            InventoryLocation.warehouse_id == warehouse_id,
        ).order_by(InventoryLocation.code).all()

    def get(self, db: Session, *, company_id: int, location_id: int):
        return db.query(InventoryLocation).filter(
            InventoryLocation.id == location_id,
            InventoryLocation.company_id == company_id,
        ).first()


location_repository = LocationRepository()
