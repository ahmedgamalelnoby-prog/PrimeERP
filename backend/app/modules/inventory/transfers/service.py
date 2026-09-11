from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.stock_moves.schemas import StockMoveCreate
from app.modules.inventory.stock_moves.service import inventory_stock_move_service
from app.modules.inventory.transfers.models import InventoryTransfer, InventoryTransferLine
from app.modules.inventory.warehouses.models import InventoryWarehouse


class InventoryTransferService:
    def get(self, db: Session, *, company_id: int, transfer_id: int):
        return db.scalar(
            select(InventoryTransfer)
            .where(InventoryTransfer.id == transfer_id, InventoryTransfer.company_id == company_id)
            .options(selectinload(InventoryTransfer.lines))
        )

    def list(self, db: Session, *, company_id: int, status: str | None = None):
        stmt = select(InventoryTransfer).where(InventoryTransfer.company_id == company_id)
        if status:
            stmt = stmt.where(InventoryTransfer.status == status)
        return list(db.scalars(stmt.order_by(InventoryTransfer.id.desc())))

    def create(self, db: Session, payload):
        if payload.source_warehouse_id == payload.destination_warehouse_id:
            raise ValueError("Source and destination warehouses must be different")

        source = self._warehouse(db, payload.company_id, payload.source_warehouse_id)
        destination = self._warehouse(db, payload.company_id, payload.destination_warehouse_id)
        if source is None or destination is None:
            raise ValueError("Source or destination warehouse is invalid")

        transfer = InventoryTransfer(
            company_id=payload.company_id,
            source_warehouse_id=payload.source_warehouse_id,
            destination_warehouse_id=payload.destination_warehouse_id,
            reference=payload.reference.strip(),
            notes=payload.notes,
            status="draft",
        )
        db.add(transfer)
        db.flush()

        for line in payload.lines:
            item = db.scalar(
                select(InventoryItem).where(
                    InventoryItem.id == line.item_id,
                    InventoryItem.company_id == payload.company_id,
                    InventoryItem.is_active.is_(True),
                )
            )
            if item is None:
                raise ValueError(f"Item {line.item_id} is invalid for this company")

            src = self._location(db, payload.company_id, line.source_location_id)
            dst = self._location(db, payload.company_id, line.destination_location_id)
            if src is None or dst is None:
                raise ValueError("Transfer location is invalid")
            if src.warehouse_id != source.id or dst.warehouse_id != destination.id:
                raise ValueError("Transfer locations do not belong to the selected warehouses")

            db.add(
                InventoryTransferLine(
                    transfer_id=transfer.id,
                    item_id=line.item_id,
                    source_location_id=line.source_location_id,
                    destination_location_id=line.destination_location_id,
                    quantity=line.quantity,
                    unit_cost=line.unit_cost,
                )
            )
        db.flush()
        return transfer

    def request(self, db: Session, *, company_id: int, transfer_id: int):
        return self._transition(db, company_id, transfer_id, "draft", "requested")

    def approve(self, db: Session, *, company_id: int, transfer_id: int):
        return self._transition(db, company_id, transfer_id, "requested", "approved")

    def ship(self, db: Session, *, company_id: int, transfer_id: int):
        transfer = self._locked(db, company_id, transfer_id)
        if transfer is None:
            raise ValueError("Transfer not found")
        if transfer.status != "approved":
            raise ValueError("Only approved transfers can be shipped")
        if not transfer.lines:
            raise ValueError("Transfer has no lines")

        for line in transfer.lines:
            move = inventory_stock_move_service.create_draft(
                db,
                StockMoveCreate(
                    company_id=company_id,
                    item_id=line.item_id,
                    source_location_id=line.source_location_id,
                    destination_location_id=None,
                    quantity=line.quantity,
                    unit_cost=line.unit_cost,
                    movement_type="issue",
                    reference=transfer.reference,
                    source_module="inventory/transfers",
                    source_entity="inventory_transfer",
                    source_id=str(transfer.id),
                ),
            )
            inventory_stock_move_service.post(db, company_id=company_id, move_id=move.id)
            line.shipped_quantity = line.quantity

        transfer.status = "shipped"
        db.flush()
        return transfer

    def receive(self, db: Session, *, company_id: int, transfer_id: int):
        transfer = self._locked(db, company_id, transfer_id)
        if transfer is None:
            raise ValueError("Transfer not found")
        if transfer.status != "shipped":
            raise ValueError("Only shipped transfers can be received")

        for line in transfer.lines:
            if line.received_quantity >= line.shipped_quantity:
                continue
            quantity = line.shipped_quantity - line.received_quantity
            move = inventory_stock_move_service.create_draft(
                db,
                StockMoveCreate(
                    company_id=company_id,
                    item_id=line.item_id,
                    source_location_id=None,
                    destination_location_id=line.destination_location_id,
                    quantity=quantity,
                    unit_cost=line.unit_cost,
                    movement_type="receipt",
                    reference=transfer.reference,
                    source_module="inventory/transfers",
                    source_entity="inventory_transfer",
                    source_id=str(transfer.id),
                ),
            )
            inventory_stock_move_service.post(db, company_id=company_id, move_id=move.id)
            line.received_quantity = line.shipped_quantity

        transfer.status = "received"
        db.flush()
        return transfer

    def cancel(self, db: Session, *, company_id: int, transfer_id: int):
        transfer = self._locked(db, company_id, transfer_id)
        if transfer is None:
            raise ValueError("Transfer not found")
        if transfer.status not in {"draft", "requested", "approved"}:
            raise ValueError("Only unshipped transfers can be cancelled")
        transfer.status = "cancelled"
        db.flush()
        return transfer

    @staticmethod
    def _warehouse(db: Session, company_id: int, warehouse_id: int):
        return db.scalar(
            select(InventoryWarehouse).where(
                InventoryWarehouse.id == warehouse_id,
                InventoryWarehouse.company_id == company_id,
                InventoryWarehouse.is_active.is_(True),
            )
        )

    @staticmethod
    def _location(db: Session, company_id: int, location_id: int):
        return db.scalar(
            select(InventoryLocation).where(
                InventoryLocation.id == location_id,
                InventoryLocation.company_id == company_id,
                InventoryLocation.is_active.is_(True),
            )
        )

    @staticmethod
    def _locked(db: Session, company_id: int, transfer_id: int):
        return db.scalar(
            select(InventoryTransfer)
            .where(InventoryTransfer.id == transfer_id, InventoryTransfer.company_id == company_id)
            .options(selectinload(InventoryTransfer.lines))
            .with_for_update()
        )

    def _transition(self, db: Session, company_id: int, transfer_id: int, current: str, target: str):
        transfer = self._locked(db, company_id, transfer_id)
        if transfer is None:
            raise ValueError("Transfer not found")
        if transfer.status != current:
            raise ValueError(f"Transfer must be {current} before it can become {target}")
        transfer.status = target
        db.flush()
        return transfer


inventory_transfer_service = InventoryTransferService()
