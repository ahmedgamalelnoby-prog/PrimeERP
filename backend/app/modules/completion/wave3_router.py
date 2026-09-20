from __future__ import annotations

from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.companies.models import Company
from app.modules.inventory.items.models import InventoryStock
from app.modules.inventory.stock_moves.models import InventoryStockMove
from app.modules.pos.completion_models import POSPromotionUse
from app.modules.restaurant.models import PosOrderLineRoute, PosTerminal, PosOutlet
from app.modules.commerce.models import SalesDocument, SalesLine, CommercePayment
from app.modules.shipping.models import Shipment
from app.modules.treasury.completion_models import TreasuryTransaction

router = APIRouter(prefix="/completion/wave3", tags=["Completion Wave 3"])


def _company(db: Session, company_id: int, user: User) -> Company:
    if user.tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(
        select(Company).where(
            Company.id == company_id,
            Company.tenant_id == user.tenant_id,
            Company.is_active.is_(True),
        )
    )
    if company is None:
        raise HTTPException(403, "Company is outside the current tenant")
    return company


class KDSStatusPayload(BaseModel):
    status: str = Field(min_length=1, max_length=20)
    notes: str | None = Field(default=None, max_length=500)


@router.get("/inventory/exceptions", dependencies=[Depends(require_permission("inventory.access"))])
def inventory_exceptions(
    company_id: int = Query(..., gt=0),
    warehouse_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _company(db, company_id, user)
    stmt = select(InventoryStock).where(InventoryStock.company_id == company_id)
    if warehouse_id is not None:
        stmt = stmt.where(InventoryStock.warehouse_id == warehouse_id)
    rows = db.scalars(stmt.order_by(InventoryStock.warehouse_id, InventoryStock.item_id)).all()
    result = []
    for row in rows:
        qty = Decimal(str(row.quantity_on_hand or 0))
        cost = Decimal(str(row.average_cost or 0))
        if qty < 0:
            severity = "critical"
        elif qty == 0:
            severity = "warning"
        else:
            continue
        result.append({
            "warehouse_id": row.warehouse_id,
            "item_id": row.item_id,
            "quantity_on_hand": qty,
            "average_cost": cost,
            "stock_value": qty * cost,
            "severity": severity,
        })
    return {"count": len(result), "items": result}


@router.get("/inventory/movement-control", dependencies=[Depends(require_permission("inventory.access"))])
def inventory_movement_control(
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _company(db, company_id, user)
    rows = db.execute(
        select(
            InventoryStockMove.status,
            func.count(InventoryStockMove.id),
        )
        .where(InventoryStockMove.company_id == company_id)
        .group_by(InventoryStockMove.status)
        .order_by(InventoryStockMove.status)
    ).all()
    return {
        "company_id": company_id,
        "by_status": [{"status": status, "count": count} for status, count in rows],
    }


@router.get("/pos/kds", dependencies=[Depends(require_permission("commerce.access"))])
def kds_queue(
    company_id: int = Query(..., gt=0),
    station_id: int | None = Query(default=None, gt=0),
    status: str | None = Query(default=None, max_length=20),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _company(db, company_id, user)
    stmt = (
        select(PosOrderLineRoute, SalesLine, SalesDocument, PosTerminal, PosOutlet)
        .join(SalesLine, SalesLine.id == PosOrderLineRoute.sales_line_id)
        .join(SalesDocument, SalesDocument.id == SalesLine.document_id)
        .join(PosTerminal, PosTerminal.id == PosOrderLineRoute.terminal_id)
        .join(PosOutlet, PosOutlet.id == PosTerminal.outlet_id)
        .where(SalesDocument.company_id == company_id)
    )
    if station_id is not None:
        stmt = stmt.where(PosOrderLineRoute.station_id == station_id)
    if status is not None:
        stmt = stmt.where(PosOrderLineRoute.status == status)
    rows = db.execute(stmt.order_by(PosOrderLineRoute.created_at, PosOrderLineRoute.id)).all()
    return [{
        "route_id": route.id,
        "sales_document_id": doc.id,
        "sales_line_id": line.id,
        "item_id": line.item_id,
        "variant_id": line.variant_id,
        "quantity": line.quantity,
        "station_id": route.station_id,
        "terminal_id": terminal.id,
        "outlet_id": outlet.id,
        "outlet_name": outlet.name,
        "status": route.status,
        "notes": route.notes,
    } for route, line, doc, terminal, outlet in rows]


@router.post("/pos/kds/{route_id}/status", dependencies=[Depends(require_permission("commerce.write"))])
def update_kds_status(
    route_id: int,
    payload: KDSStatusPayload,
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _company(db, company_id, user)
    route = db.scalar(
        select(PosOrderLineRoute)
        .join(SalesLine, SalesLine.id == PosOrderLineRoute.sales_line_id)
        .join(SalesDocument, SalesDocument.id == SalesLine.document_id)
        .where(PosOrderLineRoute.id == route_id, SalesDocument.company_id == company_id)
        .with_for_update()
    )
    if route is None:
        raise HTTPException(404, "KDS route not found")
    allowed = {
        "queued": {"preparing", "cancelled"},
        "preparing": {"ready", "cancelled"},
        "ready": {"served", "cancelled"},
        "served": set(),
        "cancelled": set(),
    }
    target = payload.status.strip().lower()
    if target not in allowed:
        raise HTTPException(422, "Unsupported KDS status")
    if target != route.status and target not in allowed.get(route.status, set()):
        raise HTTPException(409, f"Invalid KDS transition: {route.status} -> {target}")
    if target != route.status:
        route.status = target
    if payload.notes is not None:
        route.notes = payload.notes
    db.commit()
    db.refresh(route)
    return route


@router.get("/pos/outlet-profitability", dependencies=[Depends(require_permission("commerce.access"))])
def outlet_profitability(
    company_id: int = Query(..., gt=0),
    outlet_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _company(db, company_id, user)
    stmt = (
        select(
            PosOutlet.id,
            PosOutlet.name,
            func.coalesce(func.sum(SalesLine.line_total), 0),
            func.coalesce(func.sum(SalesLine.quantity), 0),
        )
        .join(PosTerminal, PosTerminal.outlet_id == PosOutlet.id)
        .join(PosOrderLineRoute, PosOrderLineRoute.terminal_id == PosTerminal.id)
        .join(SalesLine, SalesLine.id == PosOrderLineRoute.sales_line_id)
        .join(SalesDocument, SalesDocument.id == SalesLine.document_id)
        .where(PosOutlet.company_id == company_id, SalesDocument.status.notin_(("draft", "cancelled")))
        .group_by(PosOutlet.id, PosOutlet.name)
    )
    if outlet_id is not None:
        stmt = stmt.where(PosOutlet.id == outlet_id)
    rows = db.execute(stmt).all()
    return [{
        "outlet_id": oid,
        "outlet_name": name,
        "sales_value": Decimal(str(sales or 0)),
        "quantity": Decimal(str(qty or 0)),
    } for oid, name, sales, qty in rows]


@router.get("/commerce/fulfillment-control", dependencies=[Depends(require_permission("commerce.access"))])
def fulfillment_control(
    company_id: int = Query(..., gt=0),
    document_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _company(db, company_id, user)
    stmt = select(SalesDocument).where(SalesDocument.company_id == company_id)
    if document_id is not None:
        stmt = stmt.where(SalesDocument.id == document_id)
    documents = db.scalars(stmt.order_by(SalesDocument.id.desc())).all()
    result = []
    for doc in documents:
        lines = db.scalars(select(SalesLine).where(SalesLine.document_id == doc.id)).all()
        ordered = sum((Decimal(str(x.quantity or 0)) for x in lines), Decimal("0"))
        fulfilled = sum((Decimal(str(x.fulfilled_quantity or 0)) for x in lines), Decimal("0"))
        pending = max(ordered - fulfilled, Decimal("0"))
        if fulfilled == 0:
            fulfillment = "unfulfilled"
        elif pending > 0:
            fulfillment = "partial"
        else:
            fulfillment = "fulfilled"
        move_count = db.scalar(
            select(func.count(InventoryStockMove.id)).where(
                InventoryStockMove.company_id == company_id,
                InventoryStockMove.source_entity == "sales_delivery",
                InventoryStockMove.source_id == str(doc.id),
            )
        ) or 0
        result.append({
            "document_id": doc.id,
            "number": doc.number,
            "status": doc.status,
            "ordered_quantity": ordered,
            "fulfilled_quantity": fulfilled,
            "pending_quantity": pending,
            "fulfillment_status": fulfillment,
            "stock_delivery_moves": move_count,
        })
    return result


@router.get("/shipping/control-tower", dependencies=[Depends(require_permission("commerce.access"))])
def shipping_control_tower(
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _company(db, company_id, user)
    rows = db.execute(
        select(Shipment.status, func.count(Shipment.id))
        .where(Shipment.company_id == company_id)
        .group_by(Shipment.status)
        .order_by(Shipment.status)
    ).all()
    return {"company_id": company_id, "by_status": [{"status": s, "count": c} for s, c in rows]}


@router.get("/treasury/control-tower", dependencies=[Depends(require_permission("treasury.access"))])
def treasury_control_tower(
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _company(db, company_id, user)
    rows = db.execute(
        select(
            TreasuryTransaction.status,
            func.count(TreasuryTransaction.id),
            func.coalesce(func.sum(TreasuryTransaction.amount), 0),
        )
        .where(TreasuryTransaction.company_id == company_id)
        .group_by(TreasuryTransaction.status)
        .order_by(TreasuryTransaction.status)
    ).all()
    return {
        "company_id": company_id,
        "by_status": [
            {"status": status, "count": count, "amount": Decimal(str(amount or 0))}
            for status, count, amount in rows
        ],
    }


@router.get("/finance/receivables-control", dependencies=[Depends(require_permission("commerce.access"))])
def receivables_control(
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _company(db, company_id, user)
    rows = db.execute(
        select(
            SalesDocument.status,
            func.count(SalesDocument.id),
            func.coalesce(func.sum(SalesDocument.total), 0),
            func.coalesce(func.sum(SalesDocument.paid_total), 0),
        )
        .where(SalesDocument.company_id == company_id, SalesDocument.document_type.in_(("invoice", "order")))
        .group_by(SalesDocument.status)
        .order_by(SalesDocument.status)
    ).all()
    return [{
        "status": status,
        "document_count": count,
        "gross_total": Decimal(str(total or 0)),
        "paid_total": Decimal(str(paid or 0)),
        "outstanding_total": Decimal(str(total or 0)) - Decimal(str(paid or 0)),
    } for status, count, total, paid in rows]


@router.get("/control-tower", dependencies=[Depends(require_permission("commerce.access"))])
def control_tower(
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _company(db, company_id, user)
    negative_stock = db.scalar(
        select(func.count(InventoryStock.item_id)).where(
            InventoryStock.company_id == company_id,
            InventoryStock.quantity_on_hand < 0,
        )
    ) or 0
    queued_kds = db.scalar(
        select(func.count(PosOrderLineRoute.id))
        .join(SalesLine, SalesLine.id == PosOrderLineRoute.sales_line_id)
        .join(SalesDocument, SalesDocument.id == SalesLine.document_id)
        .where(
            SalesDocument.company_id == company_id,
            PosOrderLineRoute.status.in_(("queued", "preparing")),
        )
    ) or 0
    open_shipments = db.scalar(
        select(func.count(Shipment.id)).where(
            Shipment.company_id == company_id,
            Shipment.status.notin_(("delivered", "returned", "cancelled")),
        )
    ) or 0
    posted_payments = db.scalar(
        select(func.count(CommercePayment.id)).where(
            CommercePayment.company_id == company_id,
            CommercePayment.status == "posted",
        )
    ) or 0
    return {
        "company_id": company_id,
        "inventory_negative_stock": negative_stock,
        "pos_active_kds_lines": queued_kds,
        "shipping_open_shipments": open_shipments,
        "posted_commerce_payments": posted_payments,
    }
