from __future__ import annotations

from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import case, func, select
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
from app.modules.commerce.models import SalesDocument, SalesLine, CommercePayment, PurchaseDocument, CommercePaymentAllocation, BusinessPartner
from app.modules.shipping.models import Shipment, ShippingCarrier
from app.modules.treasury.completion_models import TreasuryTransaction, TreasuryDailyClosing, TreasuryForecast\nfrom app.modules.treasury.models import Cheque, ChequeEvent\nfrom app.modules.commerce.accounting_models import CommerceAccountingSettings\nfrom app.modules.accounting.journals.models.journal_entry import JournalEntry\nfrom app.modules.accounting.journals.models.journal_entry_line import JournalEntryLine
from app.modules.manufacturing.completion_models import ManufacturingWorkOrder, ManufacturingVariance, ManufacturingConsumption
from app.modules.catalog.models import Recipe, RecipeSkuMapping
from app.modules.integrations.models import IntegrationProductMapping, IntegrationConnection

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


@router.get("/manufacturing/control-tower", dependencies=[Depends(require_permission("inventory.access"))])
def manufacturing_control_tower(
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _company(db, company_id, user)
    rows = db.execute(
        select(
            ManufacturingWorkOrder.status,
            func.count(ManufacturingWorkOrder.id),
            func.coalesce(func.sum(ManufacturingWorkOrder.planned_qty), 0),
            func.coalesce(func.sum(ManufacturingWorkOrder.completed_qty), 0),
        )
        .where(ManufacturingWorkOrder.company_id == company_id)
        .group_by(ManufacturingWorkOrder.status)
        .order_by(ManufacturingWorkOrder.status)
    ).all()
    variances = db.execute(
        select(
            func.count(ManufacturingVariance.id),
            func.coalesce(func.sum(ManufacturingVariance.total_variance), 0),
        )
        .where(ManufacturingVariance.company_id == company_id, ManufacturingVariance.status == "calculated")
    ).one()
    return {
        "company_id": company_id,
        "work_orders": [
            {
                "status": status,
                "count": count,
                "planned_quantity": Decimal(str(planned or 0)),
                "completed_quantity": Decimal(str(completed or 0)),
            }
            for status, count, planned, completed in rows
        ],
        "unposted_variance_count": variances[0] or 0,
        "unposted_variance_value": Decimal(str(variances[1] or 0)),
    }


@router.get("/integrations/salla-readiness", dependencies=[Depends(require_permission("integrations.access"))])
def salla_readiness(
    company_id: int = Query(..., gt=0),
    connection_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _company(db, company_id, user)
    connection = db.scalar(
        select(IntegrationConnection).where(
            IntegrationConnection.id == connection_id,
            IntegrationConnection.company_id == company_id,
            IntegrationConnection.provider.ilike("salla"),
            IntegrationConnection.is_active.is_(True),
        )
    )
    if connection is None:
        raise HTTPException(404, "Active Salla connection not found")
    mappings = db.scalars(
        select(IntegrationProductMapping)
        .where(
            IntegrationProductMapping.company_id == company_id,
            IntegrationProductMapping.connection_id == connection_id,
            IntegrationProductMapping.sync_status == "active",
        )
        .order_by(IntegrationProductMapping.id)
    ).all()
    result = []
    for mapping in mappings:
        recipe = db.scalar(
            select(Recipe)
            .where(
                Recipe.company_id == company_id,
                Recipe.product_id == mapping.product_id,
                Recipe.is_active.is_(True),
                Recipe.variant_id == mapping.variant_id,
            )
            .order_by(Recipe.version.desc(), Recipe.id.desc())
        )
        sku_recipe = db.scalar(
            select(RecipeSkuMapping)
            .where(
                RecipeSkuMapping.company_id == company_id,
                RecipeSkuMapping.product_id == mapping.product_id,
                RecipeSkuMapping.variant_id == mapping.variant_id,
                RecipeSkuMapping.sku == mapping.external_sku,
                RecipeSkuMapping.is_active.is_(True),
            )
        ) if mapping.external_sku else None
        result.append({
            "mapping_id": mapping.id,
            "external_id": mapping.external_id,
            "external_sku": mapping.external_sku,
            "product_id": mapping.product_id,
            "variant_id": mapping.variant_id,
            "mapped": True,
            "recipe_ready": recipe is not None or sku_recipe is not None,
            "recipe_id": recipe.id if recipe else (sku_recipe.recipe_id if sku_recipe else None),
            "sync_status": mapping.sync_status,
        })
    missing_recipe = sum(1 for row in result if not row["recipe_ready"])
    return {
        "connection_id": connection_id,
        "mapped_products": len(result),
        "missing_recipe": missing_recipe,
        "ready": missing_recipe == 0,
        "items": result,
    }


@router.get("/finance/integration-tower", dependencies=[Depends(require_permission("commerce.access"))])
def finance_integration_tower(
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _company(db, company_id, user)

    sales = db.scalars(
        select(SalesDocument).where(
            SalesDocument.company_id == company_id,
            SalesDocument.document_type.in_(("invoice", "order")),
            SalesDocument.status.notin_(("draft", "cancelled")),
        )
    ).all()
    purchases = db.scalars(
        select(PurchaseDocument).where(
            PurchaseDocument.company_id == company_id,
            PurchaseDocument.document_type.in_(("bill", "order")),
            PurchaseDocument.status.notin_(("draft", "cancelled")),
        )
    ).all()

    ar_total = sum((Decimal(str(x.total or 0)) - Decimal(str(x.paid_total or 0)) for x in sales), Decimal("0"))
    ap_total = sum((Decimal(str(x.total or 0)) - Decimal(str(x.paid_total or 0)) for x in purchases), Decimal("0"))

    payments = db.scalars(
        select(CommercePayment).where(
            CommercePayment.company_id == company_id,
            CommercePayment.status == "posted",
        )
    ).all()
    allocation_mismatches = []
    for payment in payments:
        allocated = db.scalar(
            select(func.coalesce(func.sum(CommercePaymentAllocation.amount), 0)).where(
                CommercePaymentAllocation.company_id == company_id,
                CommercePaymentAllocation.payment_id == payment.id,
                CommercePaymentAllocation.status == "active",
            )
        ) or 0
        difference = Decimal(str(payment.amount or 0)) - Decimal(str(allocated or 0))
        if difference != 0:
            allocation_mismatches.append({
                "payment_id": payment.id,
                "amount": Decimal(str(payment.amount or 0)),
                "allocated": Decimal(str(allocated or 0)),
                "difference": difference,
            })

    carrier_rows = db.execute(
        select(
            ShippingCarrier.id,
            ShippingCarrier.name,
            func.count(Shipment.id),
            func.coalesce(func.sum(Shipment.cod_collected), 0),
            func.coalesce(func.sum(Shipment.shipping_fee), 0),
        )
        .outerjoin(Shipment, Shipment.carrier_id == ShippingCarrier.id)
        .where(ShippingCarrier.company_id == company_id)
        .group_by(ShippingCarrier.id, ShippingCarrier.name)
        .order_by(ShippingCarrier.id)
    ).all()

    return {
        "company_id": company_id,
        "receivables": {
            "document_count": len(sales),
            "outstanding": ar_total,
        },
        "payables": {
            "document_count": len(purchases),
            "outstanding": ap_total,
        },
        "payment_reconciliation": {
            "posted_payment_count": len(payments),
            "allocation_mismatch_count": len(allocation_mismatches),
            "mismatches": allocation_mismatches,
        },
        "shipping_carriers": [
            {
                "carrier_id": carrier_id,
                "carrier_name": name,
                "shipment_count": count,
                "cod_collected": Decimal(str(cod or 0)),
                "shipping_fee": Decimal(str(fee or 0)),
                "net_before_other_carrier_charges": Decimal(str(cod or 0)) - Decimal(str(fee or 0)),
            }
            for carrier_id, name, count, cod, fee in carrier_rows
        ],
        "healthy": not allocation_mismatches,
    }


@router.get("/inventory/costing-tower", dependencies=[Depends(require_permission("inventory.access"))])
def inventory_costing_tower(
    company_id: int = Query(..., gt=0),
    warehouse_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _company(db, company_id, user)
    stmt = select(InventoryStock).where(InventoryStock.company_id == company_id)
    if warehouse_id is not None:
        stmt = stmt.where(InventoryStock.warehouse_id == warehouse_id)
    stocks = db.scalars(stmt).all()

    negative = []
    zero_cost = []
    total_value = Decimal("0")
    for stock in stocks:
        qty = Decimal(str(stock.quantity_on_hand or 0))
        cost = Decimal(str(stock.average_cost or 0))
        value = qty * cost
        total_value += value
        if qty < 0:
            negative.append({
                "warehouse_id": stock.warehouse_id,
                "item_id": stock.item_id,
                "quantity": qty,
                "value": value,
            })
        if qty > 0 and cost <= 0:
            zero_cost.append({
                "warehouse_id": stock.warehouse_id,
                "item_id": stock.item_id,
                "quantity": qty,
            })

    return {
        "company_id": company_id,
        "stock_value": total_value,
        "stock_rows": len(stocks),
        "negative_stock_count": len(negative),
        "zero_cost_stock_count": len(zero_cost),
        "negative_stock": negative,
        "zero_cost_stock": zero_cost,
        "healthy": not negative and not zero_cost,
    }


@router.get("/manufacturing/production-finance", dependencies=[Depends(require_permission("inventory.access"))])
def manufacturing_production_finance(
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _company(db, company_id, user)
    work_orders = db.scalars(
        select(ManufacturingWorkOrder).where(ManufacturingWorkOrder.company_id == company_id)
    ).all()
    rows = []
    for wo in work_orders:
        variance = db.scalar(
            select(ManufacturingVariance)
            .where(ManufacturingVariance.work_order_id == wo.id)
            .order_by(ManufacturingVariance.id.desc())
        )
        rows.append({
            "work_order_id": wo.id,
            "number": wo.number,
            "status": wo.status,
            "planned_quantity": Decimal(str(wo.planned_qty or 0)),
            "completed_quantity": Decimal(str(wo.completed_qty or 0)),
            "remaining_quantity": max(
                Decimal(str(wo.planned_qty or 0)) - Decimal(str(wo.completed_qty or 0)),
                Decimal("0"),
            ),
            "material_cost": Decimal(str(wo.total_material_cost or 0)),
            "labor_cost": Decimal(str(wo.total_labor_cost or 0)),
            "overhead_cost": Decimal(str(wo.total_overhead_cost or 0)),
            "variance": Decimal(str(variance.total_variance or 0)) if variance else Decimal("0"),
            "variance_status": variance.status if variance else None,
        })
    return rows


@router.get("/commerce/return-reconciliation", dependencies=[Depends(require_permission("commerce.access"))])
def return_reconciliation(
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _company(db, company_id, user)
    sales_returns = db.scalars(
        select(SalesDocument).where(
            SalesDocument.company_id == company_id,
            SalesDocument.document_type == "credit_note",
            SalesDocument.status.notin_(("draft", "cancelled")),
        )
    ).all()
    purchase_returns = db.scalars(
        select(PurchaseDocument).where(
            PurchaseDocument.company_id == company_id,
            PurchaseDocument.document_type == "debit_note",
            PurchaseDocument.status.notin_(("draft", "cancelled")),
        )
    ).all()

    def summarize(rows):
        gross = sum((Decimal(str(x.total or 0)) for x in rows), Decimal("0"))
        paid = sum((Decimal(str(x.paid_total or 0)) for x in rows), Decimal("0"))
        return {
            "count": len(rows),
            "gross_value": gross,
            "paid_value": paid,
            "unsettled_value": gross - paid,
        }

    return {
        "company_id": company_id,
        "sales_returns": summarize(sales_returns),
        "purchase_returns": summarize(purchase_returns),
    }


@router.get("/shipping/cod-reconciliation", dependencies=[Depends(require_permission("commerce.access"))])
def shipping_cod_reconciliation(
    company_id: int = Query(..., gt=0),
    carrier_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _company(db, company_id, user)
    stmt = select(Shipment).where(
        Shipment.company_id == company_id,
        Shipment.status.in_(("delivered", "returned")),
    )
    if carrier_id is not None:
        stmt = stmt.where(Shipment.carrier_id == carrier_id)
    rows = db.scalars(stmt.order_by(Shipment.id)).all()

    delivered_cod = Decimal("0")
    returned_cod = Decimal("0")
    fees = Decimal("0")
    for shipment in rows:
        cod = Decimal(str(shipment.cod_collected or 0))
        fee = Decimal(str(shipment.shipping_fee or 0))
        fees += fee
        if shipment.status == "delivered":
            delivered_cod += cod
        else:
            returned_cod += cod

    return {
        "company_id": company_id,
        "carrier_id": carrier_id,
        "shipment_count": len(rows),
        "delivered_cod": delivered_cod,
        "returned_cod": returned_cod,
        "shipping_fees": fees,
        "net_cod_after_shipping_fees": delivered_cod - fees,
    }


@router.get("/treasury/cheque-integration", dependencies=[Depends(require_permission("treasury.access"))])
def cheque_integration(
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _company(db, company_id, user)
    cheque_rows = db.execute(
        select(
            Cheque.status,
            Cheque.direction,
            func.count(Cheque.id),
            func.coalesce(func.sum(Cheque.amount), 0),
        )
        .where(Cheque.company_id == company_id)
        .group_by(Cheque.status, Cheque.direction)
        .order_by(Cheque.direction, Cheque.status)
    ).all()
    events_count = db.scalar(
        select(func.count(ChequeEvent.id)).where(ChequeEvent.company_id == company_id)
    ) or 0
    return {
        "company_id": company_id,
        "cheques": [
            {
                "status": status,
                "direction": direction,
                "count": count,
                "amount": Decimal(str(amount or 0)),
            }
            for status, direction, count, amount in cheque_rows
        ],
        "event_count": events_count,
        "terminal_statuses": ["collected", "cleared", "cancelled", "reversed", "withdrawn"],
    }


@router.get("/treasury/reconciliation-control", dependencies=[Depends(require_permission("treasury.access"))])
def treasury_reconciliation_control(
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _company(db, company_id, user)

    posted = db.execute(
        select(
            TreasuryTransaction.account_id,
            func.coalesce(
                func.sum(
                    case(
                        (TreasuryTransaction.transaction_type.in_(("receipt", "deposit")), TreasuryTransaction.amount),
                        (TreasuryTransaction.transaction_type.in_(("payment", "withdrawal")), -TreasuryTransaction.amount),
                        else_=0,
                    )
                ),
                0,
            ),
        )
        .where(
            TreasuryTransaction.company_id == company_id,
            TreasuryTransaction.status == "posted",
        )
        .group_by(TreasuryTransaction.account_id)
    ).all()

    closing = db.execute(
        select(
            func.count(TreasuryDailyClosing.id),
            func.coalesce(func.sum(TreasuryDailyClosing.difference), 0),
        )
        .where(
            TreasuryDailyClosing.company_id == company_id,
            TreasuryDailyClosing.status == "closed",
        )
    ).one()

    forecast = db.execute(
        select(
            func.count(TreasuryForecast.id),
            func.coalesce(func.sum(TreasuryForecast.expected_inflow), 0),
            func.coalesce(func.sum(TreasuryForecast.expected_outflow), 0),
        )
        .where(TreasuryForecast.company_id == company_id)
    ).one()

    return {
        "company_id": company_id,
        "posted_account_positions": [
            {"account_id": account_id, "balance": Decimal(str(balance or 0))}
            for account_id, balance in posted
        ],
        "daily_closing": {
            "closed_days": closing[0] or 0,
            "net_difference": Decimal(str(closing[1] or 0)),
        },
        "forecast": {
            "forecast_count": forecast[0] or 0,
            "expected_inflow": Decimal(str(forecast[1] or 0)),
            "expected_outflow": Decimal(str(forecast[2] or 0)),
            "expected_net": Decimal(str(forecast[1] or 0)) - Decimal(str(forecast[2] or 0)),
        },
    }


@router.get("/treasury/gl-reconciliation", dependencies=[Depends(require_permission("treasury.access"))])
def treasury_gl_reconciliation(
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _company(db, company_id, user)
    settings = db.scalar(
        select(CommerceAccountingSettings).where(CommerceAccountingSettings.company_id == company_id)
    )
    if settings is None:
        raise HTTPException(409, "Accounting configuration is required for treasury GL reconciliation")

    treasury_rows = db.execute(
        select(
            TreasuryTransaction.account_id,
            func.sum(
                case(
                    (TreasuryTransaction.transaction_type.in_(("receipt", "deposit")), TreasuryTransaction.amount),
                    (TreasuryTransaction.transaction_type.in_(("payment", "withdrawal")), -TreasuryTransaction.amount),
                    (TreasuryTransaction.transaction_type == "transfer", -TreasuryTransaction.amount),
                    else_=0,
                )
            ),
        )
        .where(
            TreasuryTransaction.company_id == company_id,
            TreasuryTransaction.status == "posted",
        )
        .group_by(TreasuryTransaction.account_id)
    ).all()
    destination_rows = db.execute(
        select(TreasuryTransaction.offset_account_id, func.sum(TreasuryTransaction.amount))
        .where(
            TreasuryTransaction.company_id == company_id,
            TreasuryTransaction.status == "posted",
            TreasuryTransaction.transaction_type == "transfer",
        )
        .group_by(TreasuryTransaction.offset_account_id)
    ).all()

    treasury = {account_id: Decimal(str(balance or 0)) for account_id, balance in treasury_rows}
    for account_id, amount in destination_rows:
        treasury[account_id] = treasury.get(account_id, Decimal("0")) + Decimal(str(amount or 0))

    gl_rows = db.execute(
        select(
            JournalEntryLine.account_combination_id,
            func.coalesce(func.sum(JournalEntryLine.debit), 0),
            func.coalesce(func.sum(JournalEntryLine.credit), 0),
        )
        .join(JournalEntry, JournalEntry.id == JournalEntryLine.entry_id)
        .where(
            JournalEntry.company_id == company_id,
            JournalEntry.status == "posted",
            JournalEntryLine.account_combination_id == settings.default_payment_account_id,
        )
        .group_by(JournalEntryLine.account_combination_id)
    ).all()
    gl_balance = Decimal("0")
    if gl_rows:
        _, debit, credit = gl_rows[0]
        gl_balance = Decimal(str(debit or 0)) - Decimal(str(credit or 0))
    treasury_balance = treasury.get(settings.default_payment_account_id, Decimal("0"))
    difference = treasury_balance - gl_balance

    return {
        "company_id": company_id,
        "account_id": settings.default_payment_account_id,
        "treasury_balance": treasury_balance,
        "gl_balance": gl_balance,
        "difference": difference,
        "reconciled": difference == 0,
    }


@router.get("/integration/end-to-end-readiness", dependencies=[Depends(require_permission("commerce.access"))])
def end_to_end_readiness(
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
    posted_payment_mismatches = 0
    payments = db.scalars(
        select(CommercePayment).where(
            CommercePayment.company_id == company_id,
            CommercePayment.status == "posted",
        )
    ).all()
    for payment in payments:
        allocated = db.scalar(
            select(func.coalesce(func.sum(CommercePaymentAllocation.amount), 0)).where(
                CommercePaymentAllocation.company_id == company_id,
                CommercePaymentAllocation.payment_id == payment.id,
                CommercePaymentAllocation.status == "active",
            )
        ) or 0
        if Decimal(str(payment.amount or 0)) != Decimal(str(allocated or 0)):
            posted_payment_mismatches += 1

    open_shipments = db.scalar(
        select(func.count(Shipment.id)).where(
            Shipment.company_id == company_id,
            Shipment.status.notin_(("delivered", "returned", "cancelled")),
        )
    ) or 0
    open_work_orders = db.scalar(
        select(func.count(ManufacturingWorkOrder.id)).where(
            ManufacturingWorkOrder.company_id == company_id,
            ManufacturingWorkOrder.status.in_(("released", "in_progress")),
        )
    ) or 0

    return {
        "company_id": company_id,
        "inventory": {"negative_stock": negative_stock},
        "payments": {"allocation_mismatches": posted_payment_mismatches},
        "shipping": {"open_shipments": open_shipments},
        "manufacturing": {"open_work_orders": open_work_orders},
        "readiness": {
            "inventory_ok": negative_stock == 0,
            "payments_ok": posted_payment_mismatches == 0,
            "operational_flow_visible": True,
        },
    }
