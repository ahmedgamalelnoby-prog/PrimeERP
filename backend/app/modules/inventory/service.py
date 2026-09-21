from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.modules.branches.models import Branch
from app.modules.products.models import Product
from .models import Warehouse,WarehouseLocation,StockBalance,StockMovement,StockTransfer,StockTransferLine,StockReservation,StockReservationLine,StockIssue,StockIssueLine
class InventoryService:
    def _warehouse(self,db,tenant_id,wid):
        obj=db.scalar(select(Warehouse).where(Warehouse.id==wid,Warehouse.tenant_id==tenant_id))
        if not obj: raise HTTPException(404,"Warehouse not found")
        return obj
    def _location(self,db,tenant_id,lid):
        obj=db.scalar(select(WarehouseLocation).where(WarehouseLocation.id==lid,WarehouseLocation.tenant_id==tenant_id))
        if not obj: raise HTTPException(404,"Location not found")
        return obj
    def _product(self,db,tenant_id,pid):
        obj=db.scalar(select(Product).where(Product.id==pid,Product.tenant_id==tenant_id,Product.is_active.is_(True)))
        if not obj: raise HTTPException(404,"Product not found")
        return obj
    def _balance(self,db,tenant_id,wid,lid,pid,lock=False):
        q=select(StockBalance).where(StockBalance.tenant_id==tenant_id,StockBalance.warehouse_id==wid,StockBalance.location_id==lid,StockBalance.product_id==pid)
        if lock: q=q.with_for_update()
        obj=db.scalar(q)
        if not obj:
            obj=StockBalance(tenant_id=tenant_id,warehouse_id=wid,location_id=lid,product_id=pid,quantity=0,reserved_quantity=0); db.add(obj); db.flush()
        return obj
    def list_warehouses(self,db,tenant_id):
        return list(db.scalars(select(Warehouse).where(Warehouse.tenant_id==tenant_id).order_by(Warehouse.name,Warehouse.id)).all())
    def create_warehouse(self,db,tenant_id,payload):
        if not db.scalar(select(Branch).where(Branch.id==payload.branch_id,Branch.tenant_id==tenant_id)): raise HTTPException(404,"Branch not found")
        obj=Warehouse(tenant_id=tenant_id,**payload.model_dump()); db.add(obj)
        try: db.commit()
        except IntegrityError as exc: db.rollback(); raise HTTPException(409,"Warehouse code already exists for this tenant") from exc
        db.refresh(obj); return obj
    def list_locations(self,db,tenant_id,warehouse_id):
        self._warehouse(db,tenant_id,warehouse_id)
        return list(db.scalars(select(WarehouseLocation).where(WarehouseLocation.tenant_id==tenant_id,WarehouseLocation.warehouse_id==warehouse_id).order_by(WarehouseLocation.name,WarehouseLocation.id)).all())
    def create_location(self,db,tenant_id,payload):
        warehouse=self._warehouse(db,tenant_id,payload.warehouse_id)
        if payload.parent_id:
            parent=self._location(db,tenant_id,payload.parent_id)
            if parent.warehouse_id!=warehouse.id: raise HTTPException(400,"Parent location belongs to another warehouse")
        obj=WarehouseLocation(tenant_id=tenant_id,**payload.model_dump()); db.add(obj)
        try: db.commit()
        except IntegrityError as exc: db.rollback(); raise HTTPException(409,"Location code already exists in this warehouse") from exc
        db.refresh(obj); return obj
    def list_balances(self,db,tenant_id,warehouse_id=None,product_id=None):
        q=select(StockBalance).where(StockBalance.tenant_id==tenant_id)
        if warehouse_id is not None:q=q.where(StockBalance.warehouse_id==warehouse_id)
        if product_id is not None:q=q.where(StockBalance.product_id==product_id)
        return list(db.scalars(q.order_by(StockBalance.warehouse_id,StockBalance.location_id,StockBalance.product_id)).all())
    def post_movement(self,db,tenant_id,payload):
        warehouse=self._warehouse(db,tenant_id,payload.warehouse_id); location=self._location(db,tenant_id,payload.location_id); self._product(db,tenant_id,payload.product_id)
        if location.warehouse_id!=warehouse.id: raise HTTPException(400,"Location does not belong to warehouse")
        b=self._balance(db,tenant_id,warehouse.id,location.id,payload.product_id,True); qty=Decimal(payload.quantity)
        if payload.movement_type in {"issue","consumption","waste","transfer_out"}:
            if b.quantity-b.reserved_quantity<qty: raise HTTPException(409,"Insufficient available stock")
            b.quantity-=qty
        else:b.quantity+=qty
        m=StockMovement(tenant_id=tenant_id,product_id=payload.product_id,warehouse_id=warehouse.id,location_id=location.id,movement_type=payload.movement_type,quantity=qty,notes=payload.notes); db.add(m); db.commit(); db.refresh(m); return m
    def post_transfer(self,db,tenant_id,payload):
        source=self._warehouse(db,tenant_id,payload.source_warehouse_id); dest=self._warehouse(db,tenant_id,payload.destination_warehouse_id)
        if source.id==dest.id: raise HTTPException(400,"Source and destination warehouses must differ")
        transfer=StockTransfer(tenant_id=tenant_id,source_warehouse_id=source.id,destination_warehouse_id=dest.id,notes=payload.notes); db.add(transfer); db.flush()
        try:
            for line in payload.lines:
                sl=self._location(db,tenant_id,line.source_location_id); dl=self._location(db,tenant_id,line.destination_location_id)
                if sl.warehouse_id!=source.id or dl.warehouse_id!=dest.id: raise HTTPException(400,"Transfer locations do not match warehouses")
                self._product(db,tenant_id,line.product_id); qty=Decimal(line.quantity)
                sb=self._balance(db,tenant_id,source.id,sl.id,line.product_id,True)
                if sb.quantity-sb.reserved_quantity<qty: raise HTTPException(409,f"Insufficient available stock for product {line.product_id}")
                db.add(StockTransferLine(transfer_id=transfer.id,product_id=line.product_id,source_location_id=sl.id,destination_location_id=dl.id,quantity=qty)); sb.quantity-=qty
                db.add(StockMovement(tenant_id=tenant_id,product_id=line.product_id,warehouse_id=source.id,location_id=sl.id,movement_type="transfer_out",quantity=qty,reference_type="stock_transfer",reference_id=transfer.id))
                db.add(StockMovement(tenant_id=tenant_id,product_id=line.product_id,warehouse_id=dest.id,location_id=dl.id,movement_type="transfer_in",quantity=qty,reference_type="stock_transfer",reference_id=transfer.id))
                db.flush(); self._balance(db,tenant_id,dest.id,dl.id,line.product_id,True).quantity+=qty
            db.commit(); db.refresh(transfer); return transfer
        except Exception: db.rollback(); raise
    def reserve(self,db,tenant_id,payload):
        reservation=StockReservation(tenant_id=tenant_id,reference_type=payload.reference_type,reference_id=payload.reference_id,notes=payload.notes); db.add(reservation); db.flush()
        try:
            for line in payload.lines:
                loc=self._location(db,tenant_id,line.location_id); self._product(db,tenant_id,line.product_id); b=self._balance(db,tenant_id,loc.warehouse_id,loc.id,line.product_id,True); qty=Decimal(line.quantity)
                if b.quantity-b.reserved_quantity<qty: raise HTTPException(409,f"Insufficient available stock for product {line.product_id}")
                b.reserved_quantity+=qty; db.add(StockReservationLine(reservation_id=reservation.id,product_id=line.product_id,location_id=loc.id,quantity=qty))
            db.commit(); db.refresh(reservation); return reservation
        except Exception: db.rollback(); raise
    def issue(self,db,tenant_id,payload):
        warehouse=self._warehouse(db,tenant_id,payload.warehouse_id); issue=StockIssue(tenant_id=tenant_id,warehouse_id=warehouse.id,issue_type=payload.issue_type,reference_type=payload.reference_type,reference_id=payload.reference_id,notes=payload.notes); db.add(issue); db.flush()
        try:
            for line in payload.lines:
                loc=self._location(db,tenant_id,line.location_id)
                if loc.warehouse_id!=warehouse.id: raise HTTPException(400,"Issue location does not belong to warehouse")
                self._product(db,tenant_id,line.product_id); b=self._balance(db,tenant_id,warehouse.id,loc.id,line.product_id,True); qty=Decimal(line.quantity)
                if b.quantity-b.reserved_quantity<qty: raise HTTPException(409,f"Insufficient available stock for product {line.product_id}")
                b.quantity-=qty; db.add(StockIssueLine(issue_id=issue.id,product_id=line.product_id,location_id=loc.id,quantity=qty)); db.add(StockMovement(tenant_id=tenant_id,product_id=line.product_id,warehouse_id=warehouse.id,location_id=loc.id,movement_type=payload.issue_type,quantity=qty,reference_type="stock_issue",reference_id=issue.id))
            db.commit(); db.refresh(issue); return issue
        except Exception: db.rollback(); raise
inventory_service=InventoryService()
