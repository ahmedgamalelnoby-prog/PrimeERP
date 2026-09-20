from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.companies.models import Company
from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.warehouses.models import InventoryWarehouse
from app.modules.inventory.stock_moves.models import InventoryStockMove
from app.modules.inventory.stock_moves.schemas import StockMoveCreate
from app.modules.inventory.stock_moves.service import inventory_stock_move_service
from app.modules.audit.service import record_audit_event
from .models import WMSOperation, WMSOperationLine, InventoryTrackingUnit


class WMSService:
    def _scope(self, db, tenant_id, company_id, warehouse_id):
        company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == tenant_id))
        warehouse = db.scalar(select(InventoryWarehouse).where(InventoryWarehouse.id == warehouse_id, InventoryWarehouse.company_id == company_id, InventoryWarehouse.is_active.is_(True)))
        if not company or not warehouse:
            raise ValueError("Company or warehouse is outside the current tenant")
        return warehouse

    def create(self, db: Session, *, tenant_id: int, user_id: int, payload):
        self._scope(db, tenant_id, payload.company_id, payload.warehouse_id)
        if db.scalar(select(WMSOperation).where(WMSOperation.company_id == payload.company_id, WMSOperation.reference == payload.reference)):
            raise ValueError("WMS reference already exists")
        op = WMSOperation(company_id=payload.company_id, warehouse_id=payload.warehouse_id, operation_type=payload.operation_type, reference=payload.reference, notes=payload.notes, created_by=user_id)
        db.add(op); db.flush()
        for line in payload.lines:
            item = db.scalar(select(InventoryItem).where(InventoryItem.id == line.item_id, InventoryItem.company_id == payload.company_id, InventoryItem.is_active.is_(True)))
            if not item:
                raise ValueError("Item does not belong to the company")
            for loc_id in (line.source_location_id, line.destination_location_id):
                if loc_id:
                    loc = db.scalar(select(InventoryLocation).where(InventoryLocation.id == loc_id, InventoryLocation.company_id == payload.company_id, InventoryLocation.warehouse_id == payload.warehouse_id, InventoryLocation.is_active.is_(True)))
                    if not loc:
                        raise ValueError("Location must belong to the selected warehouse")
            if line.serial_number and line.quantity != Decimal("1"):
                raise ValueError("A serial-tracked line must have quantity 1")
            op.lines.append(WMSOperationLine(**line.model_dump()))
        db.flush()
        return op

    def transition(self, db: Session, *, tenant_id: int, user_id: int, operation_id: int, target: str):
        op = db.scalar(select(WMSOperation).where(WMSOperation.id == operation_id).with_for_update())
        if not op: raise ValueError("WMS operation not found")
        self._scope(db, tenant_id, op.company_id, op.warehouse_id)
        allowed = {"draft":{"approved","cancelled"}, "approved":{"in_progress","cancelled"}, "in_progress":{"completed","cancelled"}, "completed":set(), "cancelled":set()}
        if target not in allowed.get(op.status, set()):
            raise ValueError(f"Invalid WMS transition {op.status} -> {target}")
        if target == "in_progress":
            self._validate_tracking(db, op)
        if target == "completed":
            self._execute(db, tenant_id, user_id, op)
            op.posted_at = datetime.now(timezone.utc)
        op.status = target
        record_audit_event(db, action="inventory.wms.transition", entity_type="inventory_wms_operation", entity_id=op.id, user_id=user_id, tenant_id=tenant_id, company_id=op.company_id, metadata={"from": op.status, "to": target, "reference": op.reference})
        return op

    def _validate_tracking(self, db, op):
        for line in op.lines:
            if line.serial_number:
                existing = db.scalar(select(InventoryTrackingUnit).where(InventoryTrackingUnit.company_id == op.company_id, InventoryTrackingUnit.item_id == line.item_id, InventoryTrackingUnit.variant_id == line.variant_id, InventoryTrackingUnit.serial_number == line.serial_number, InventoryTrackingUnit.is_active.is_(True)))
                if op.operation_type in {"receiving","cycle_count"} and existing:
                    raise ValueError("Serial number already exists in active inventory")
                if op.operation_type in {"picking","dispatch","putaway"} and not existing:
                    raise ValueError("Serial number is not present in active inventory")
            if line.expiry_date and op.operation_type in {"picking","dispatch"}:
                from datetime import date
                if line.expiry_date < date.today():
                    raise ValueError("Expired stock cannot be picked or dispatched")

    def _execute(self, db, tenant_id, user_id, op):
        if op.operation_type == "packing":
            for line in op.lines: line.processed_quantity = line.quantity
            return
        for line in op.lines:
            if line.stock_move_id:
                continue
            movement = {"receiving":"receipt","putaway":"transfer","picking":"issue","dispatch":"issue","cycle_count":"adjustment"}[op.operation_type]
            source = line.source_location_id
            dest = line.destination_location_id
            if op.operation_type == "dispatch" and not source:
                raise ValueError("Dispatch requires a shipping/source location")
            if op.operation_type == "receiving" and not dest:
                raise ValueError("Receiving requires a destination location")
            if op.operation_type == "cycle_count":
                if line.count_expected is None or line.count_actual is None:
                    raise ValueError("Cycle count requires expected and actual quantities")
                delta = Decimal(line.count_actual) - Decimal(line.count_expected)
                if delta == 0:
                    line.processed_quantity = line.quantity
                    continue
                movement = "receipt" if delta > 0 else "issue"
                line.quantity = abs(delta)
                source, dest = (None, dest) if delta > 0 else (source, None)
            payload = StockMoveCreate(company_id=op.company_id, item_id=line.item_id, variant_id=line.variant_id, source_location_id=source, destination_location_id=dest, quantity=line.quantity, unit_cost=line.unit_cost, movement_type=movement, source_module="inventory_wms", source_entity=op.operation_type, source_id=f"{op.id}:{line.id}", reference=op.reference, notes=op.notes)
            move = inventory_stock_move_service.create_draft(db, payload)
            posted = inventory_stock_move_service.post(db, tenant_id=tenant_id, company_id=op.company_id, move_id=move.id, user_id=user_id)
            line.stock_move_id = posted.id
            line.processed_quantity = line.quantity
            self._sync_tracking(db, op, line)
    
    def _sync_tracking(self, db, op, line):
        if not (line.serial_number or line.lot_number or line.barcode):
            return
        loc_id = line.destination_location_id if op.operation_type in {"receiving","putaway"} else line.source_location_id
        if not loc_id: return
        warehouse_id = op.warehouse_id
        existing = db.scalar(select(InventoryTrackingUnit).where(InventoryTrackingUnit.company_id == op.company_id, InventoryTrackingUnit.item_id == line.item_id, InventoryTrackingUnit.variant_id == line.variant_id, InventoryTrackingUnit.location_id == loc_id, InventoryTrackingUnit.lot_number == line.lot_number, InventoryTrackingUnit.serial_number == line.serial_number).with_for_update())
        qty = Decimal(line.quantity)
        if existing:
            existing.quantity = max(Decimal("0"), Decimal(existing.quantity) + (qty if op.operation_type in {"receiving","putaway"} else -qty))
            existing.is_active = existing.quantity > 0
        elif op.operation_type in {"receiving","putaway"}:
            db.add(InventoryTrackingUnit(company_id=op.company_id,item_id=line.item_id,variant_id=line.variant_id,warehouse_id=warehouse_id,location_id=loc_id,lot_number=line.lot_number,serial_number=line.serial_number,expiry_date=line.expiry_date,barcode=line.barcode,quantity=qty,is_active=True))

    def list(self, db, company_id, operation_type=None, status=None):
        q=select(WMSOperation).where(WMSOperation.company_id==company_id)
        if operation_type: q=q.where(WMSOperation.operation_type==operation_type)
        if status: q=q.where(WMSOperation.status==status)
        return db.scalars(q.order_by(WMSOperation.id.desc())).all()

wms_service = WMSService()
