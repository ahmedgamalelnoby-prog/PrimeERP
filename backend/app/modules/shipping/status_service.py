from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.shipping.cost_models import ShippingShipmentCost
from app.modules.shipping.models import Shipment
from app.modules.shipping.settlement_models import ShippingShipmentSettlement
from app.modules.shipping.status_models import ShippingFinancialEvent, ShippingOrderStatus, ShippingStatusHistory


DEFAULT_STATUSES = [
    ("pending", "New", "جديد", None, 10, []),
    ("preparing", "Under Preparation", "تحت التجهيز", None, 20, []),
    ("packing", "Packing", "في التغليف", None, 30, []),
    ("shipped", "Shipped", "تم الشحن", None, 40, []),
    ("in_transit", "In Transit", "في الطريق", None, 50, []),
    ("out_for_delivery", "Out for Delivery", "جاري التوصيل", None, 60, []),
    ("delivered", "Delivered", "تم التسليم", None, 70, [
        "recognize_revenue", "recognize_shipping_cost", "create_cod_receivable",
        "recognize_cod_fee", "recognize_card_fee"
    ]),
    ("returning", "Returning", "قيد الاسترجاع", None, 80, []),
    ("returned", "Returned", "مرتجع", None, 90, [
        "reverse_revenue", "reverse_cod_receivable", "recognize_return_cost"
    ]),
    ("cancelled", "Cancelled", "ملغي", None, 100, []),
]


class ShippingStatusService:
    def ensure_defaults(self, db: Session, company_id: int) -> None:
        existing = {x.code for x in db.scalars(select(ShippingOrderStatus).where(ShippingOrderStatus.company_id == company_id)).all()}
        for code, name, name_ar, parent, sort_order, actions in DEFAULT_STATUSES:
            if code not in existing:
                db.add(ShippingOrderStatus(company_id=company_id, code=code, name=name, name_ar=name_ar,
                                           parent_code=parent, sort_order=sort_order,
                                           financial_actions=json.dumps(actions)))
        db.flush()

    def apply_transition(self, db: Session, shipment: Shipment, new_status: str, changed_on: date | None = None) -> list[ShippingFinancialEvent]:
        changed_on = changed_on or date.today()
        self.ensure_defaults(db, shipment.company_id)
        status = db.scalar(select(ShippingOrderStatus).where(
            ShippingOrderStatus.company_id == shipment.company_id,
            ShippingOrderStatus.code == new_status,
            ShippingOrderStatus.is_active.is_(True),
        ))
        if status is None:
            raise ValueError(f"Unknown or inactive shipping status: {new_status}")
        if new_status == shipment.status:
            return []
        history = ShippingStatusHistory(shipment_id=shipment.id, from_status=shipment.status, to_status=new_status, changed_on=changed_on)
        db.add(history)
        shipment.status = new_status
        db.flush()
        actions = json.loads(status.financial_actions or "[]")
        events: list[ShippingFinancialEvent] = []
        cost = db.scalar(select(ShippingShipmentCost).where(ShippingShipmentCost.shipment_id == shipment.id))
        cost_total = Decimal(cost.total_cost or 0) if cost else Decimal(shipment.shipping_fee or 0)
        action_amounts = {
            "recognize_revenue": Decimal(shipment.order_value or 0),
            "recognize_shipping_cost": cost_total,
            "create_cod_receivable": Decimal(shipment.cod_amount or 0),
            "recognize_cod_fee": Decimal(cost.cod_fee or 0) + Decimal(cost.cod_collected_fee or 0) if cost else Decimal("0"),
            "recognize_card_fee": Decimal(cost.card_fee or 0) if cost else Decimal("0"),
            "reverse_revenue": Decimal(shipment.order_value or 0),
            "reverse_cod_receivable": Decimal(shipment.cod_amount or 0),
            "recognize_return_cost": (Decimal(cost.rto_fee or 0) if cost else Decimal("0")),
        }
        roles = {
            "recognize_revenue": ("customer_receivable", "sales_revenue"),
            "recognize_shipping_cost": ("shipping_expense", "carrier_payable"),
            "create_cod_receivable": ("carrier_cod_receivable", "customer_receivable"),
            "recognize_cod_fee": ("cod_commission_expense", "carrier_payable"),
            "recognize_card_fee": ("payment_withdrawal_fee_expense", "carrier_payable"),
            "reverse_revenue": ("sales_revenue", "customer_receivable"),
            "reverse_cod_receivable": ("customer_receivable", "carrier_cod_receivable"),
            "recognize_return_cost": ("return_shipping_expense", "carrier_payable"),
        }
        already_settled = db.scalar(select(ShippingShipmentSettlement.id).where(ShippingShipmentSettlement.shipment_id == shipment.id)) is not None
        for action in actions:
            if action == "reverse_cod_receivable" and already_settled:
                continue
            amount = action_amounts.get(action, Decimal("0"))
            if amount <= 0 or action not in roles:
                continue
            key = action
            if db.scalar(select(ShippingFinancialEvent.id).where(
                ShippingFinancialEvent.shipment_id == shipment.id,
                ShippingFinancialEvent.event_key == key,
            )):
                continue
            debit, credit = roles[action]
            is_reversal = action.startswith("reverse_")
            event = ShippingFinancialEvent(
                company_id=shipment.company_id, carrier_id=shipment.carrier_id, shipment_id=shipment.id,
                event_key=key, event_type=action, event_date=changed_on, amount=amount,
                debit_role=debit, credit_role=credit, source_status=new_status,
                is_reversal=is_reversal, description=f"Shipping financial event: {action}",
            )
            db.add(event); events.append(event)
        db.flush()
        return events


shipping_status_service = ShippingStatusService()
