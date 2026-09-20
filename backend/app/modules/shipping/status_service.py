from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.shipping.accounting_service import shipping_accounting_service
from app.modules.shipping.cost_models import ShippingShipmentCost
from app.modules.shipping.models import Shipment
from app.modules.shipping.pricing_schemas import ShippingCostInput
from app.modules.shipping.pricing_service import shipping_pricing_service
from app.modules.shipping.settlement_models import ShippingSettlementBatch, ShippingShipmentSettlement
from app.modules.shipping.status_models import ShippingFinancialEvent, ShippingOrderStatus, ShippingStatusHistory


DEFAULT_STATUSES = [
    ("pending", "New", "جديد", None, 10, []),
    ("preparing", "Under Preparation", "تحت التجهيز", None, 20, []),
    ("packing", "Packing", "في التغليف", None, 30, []),
    ("shipped", "Shipped", "تم الشحن", None, 40, []),
    ("in_transit", "In Transit", "في الطريق", None, 50, []),
    ("delivering", "Delivering", "جاري التوصيل", None, 60, []),
    ("out_for_delivery", "Out for Delivery", "خارج للتوصيل", "delivering", 61, []),
    ("delivered", "Delivered", "تم التسليم", None, 70, [
        "recognize_revenue", "recognize_shipping_revenue", "recognize_shipping_cost", "create_cod_receivable",
        "recognize_cod_fee", "recognize_payment_withdrawal_fee"
    ]),
    ("returning", "Returning", "قيد الاسترجاع", None, 80, []),
    ("failed", "Delivery Failed", "فشل التسليم", None, 75, []),
    ("rto", "Return to Origin", "مرتجع للمصدر", None, 85, ["reverse_revenue", "reverse_shipping_revenue", "reverse_cod_receivable", "recognize_return_cost"]),
    ("returned", "Returned", "مرتجع", None, 90, [
        "reverse_revenue", "reverse_shipping_revenue", "reverse_cod_receivable", "recognize_return_cost"
    ]),
    ("cancelled", "Cancelled", "ملغي", None, 100, []),
]


class ShippingStatusService:
    def ensure_defaults(self, db: Session, company_id: int) -> None:
        existing = {x.code for x in db.scalars(select(ShippingOrderStatus).where(ShippingOrderStatus.company_id == company_id)).all()}
        default_next = {
            "pending": ["preparing", "cancelled"], "preparing": ["packing", "cancelled"],
            "packing": ["shipped", "cancelled"], "shipped": ["in_transit", "cancelled"],
            "in_transit": ["delivering", "out_for_delivery", "returning"],
            "delivering": ["out_for_delivery", "delivered", "returning"],
            "out_for_delivery": ["delivered", "returning"], "delivered": ["returning", "returned"],
            "returning": ["returned"], "returned": [], "cancelled": [], "picked_up": ["in_transit"],
        }
        defaults_by_code = {row[0]: row for row in DEFAULT_STATUSES}
        for code, name, name_ar, parent, sort_order, actions in DEFAULT_STATUSES:
            if code not in existing:
                db.add(ShippingOrderStatus(company_id=company_id, code=code, name=name, name_ar=name_ar,
                                           parent_code=parent, sort_order=sort_order,
                                           financial_actions=json.dumps(actions),
                                           allowed_next_codes=json.dumps(default_next.get(code, []))))
            else:
                current = db.scalar(select(ShippingOrderStatus).where(
                    ShippingOrderStatus.company_id == company_id,
                    ShippingOrderStatus.code == code,
                ))
                # Existing rows created before transition rules were introduced must receive
                # the canonical defaults; custom edits remain untouched.
                if current is not None and (current.allowed_next_codes is None or current.allowed_next_codes == "[]"):
                    current.allowed_next_codes = json.dumps(default_next.get(code, []))
                if current is not None and (current.financial_actions is None or current.financial_actions == "[]"):
                    current.financial_actions = json.dumps(actions)
        db.flush()

    def apply_transition(self, db: Session, shipment: Shipment, new_status: str, changed_on: date | None = None, user_id: int | None = None) -> list[ShippingFinancialEvent]:
        changed_on = changed_on or date.today()
        shipment_locked = db.scalar(select(Shipment).where(Shipment.id == shipment.id, Shipment.company_id == shipment.company_id).with_for_update())
        if shipment_locked is None:
            raise ValueError("Shipment not found")
        shipment = shipment_locked
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
        old_status = shipment.status
        # Delivered is a terminal commercial state. RTO/return flows must
        # complete before delivery; a delivered shipment cannot be moved
        # backward into a return lifecycle.
        if old_status == "delivered":
            raise ValueError("Delivered shipment is final and cannot transition to another status")
        old_status_row = db.scalar(select(ShippingOrderStatus).where(
            ShippingOrderStatus.company_id == shipment.company_id,
            ShippingOrderStatus.code == old_status,
            ShippingOrderStatus.is_active.is_(True),
        ))
        if old_status_row is None:
            raise ValueError(f"Unknown or inactive current shipping status: {old_status}")
        allowed_next = json.loads(old_status_row.allowed_next_codes or "[]")
        if new_status not in allowed_next:
            raise ValueError(f"Invalid shipping status transition: {old_status} -> {new_status}")
        history = ShippingStatusHistory(shipment_id=shipment.id, from_status=old_status, to_status=new_status, changed_on=changed_on)
        db.add(history)
        shipment.status = new_status
        db.flush()
        actions = json.loads(status.financial_actions or "[]")
        events: list[ShippingFinancialEvent] = []
        cost = db.scalar(select(ShippingShipmentCost).where(ShippingShipmentCost.shipment_id == shipment.id,
            ShippingShipmentCost.company_id == shipment.company_id,
            ShippingShipmentCost.carrier_id == shipment.carrier_id,
        ))
        cost_total = Decimal(cost.total_cost or 0) if cost else Decimal(shipment.shipping_fee or 0)
        dynamic_return_cost = Decimal("0")
        if new_status == "returned":
            try:
                priced = shipping_pricing_service.calculate(db, ShippingCostInput(
                    company_id=shipment.company_id, carrier_id=shipment.carrier_id, calculation_date=changed_on,
                    zone_code=shipment.zone_code, weight_kg=shipment.weight_kg, pieces=shipment.pieces,
                    order_value=shipment.order_value, cod_amount=shipment.cod_amount, cod_collected=shipment.cod_collected,
                    card_amount=shipment.card_amount, remote_area=shipment.remote_area, shipment_status="returned",
                    storage_days=shipment.storage_days, exchange_requested=shipment.exchange_requested,
                ))
                dynamic_return_cost = Decimal(priced.surcharge_rto or 0)
            except ValueError:
                dynamic_return_cost = Decimal(cost.rto_fee or 0) if cost else Decimal("0")
        action_amounts = {
            "recognize_revenue": Decimal(shipment.order_value or 0),
            "recognize_shipping_revenue": Decimal(shipment.customer_shipping_fee or 0),
            "recognize_shipping_cost": (Decimal(cost.base_shipping or 0) + Decimal(cost.surcharge_remote or 0) + Decimal(cost.surcharge_rto or 0) + Decimal(cost.surcharge_exchange or 0) + Decimal(cost.storage_fee or 0) + Decimal(cost.other_fees or 0) + Decimal(cost.minimum_adjustment or 0)) if cost else cost_total,
            "create_cod_receivable": Decimal(shipment.cod_amount or 0),
            "recognize_cod_fee": Decimal(cost.cod_fee or 0) + Decimal(cost.cod_collected_fee or 0) if cost else Decimal("0"),
            "recognize_payment_withdrawal_fee": Decimal(cost.card_fee or 0) if cost else Decimal("0"),
            "reverse_revenue": Decimal(shipment.order_value or 0),
            "reverse_shipping_revenue": Decimal(shipment.customer_shipping_fee or 0),
            "reverse_cod_receivable": Decimal(shipment.cod_amount or 0),
            "recognize_return_cost": dynamic_return_cost,
        }
        roles = {
            "recognize_revenue": ("customer_receivable", "sales_revenue"),
            "recognize_shipping_revenue": ("customer_receivable", "shipping_revenue"),
            "recognize_shipping_cost": ("shipping_expense", "carrier_payable"),
            "create_cod_receivable": ("carrier_cod_receivable", "customer_receivable"),
            "recognize_cod_fee": ("cod_commission_expense", "carrier_payable"),
            "recognize_payment_withdrawal_fee": ("payment_withdrawal_fee_expense", "carrier_payable"),
            "reverse_revenue": ("sales_revenue", "customer_receivable"),
            "reverse_shipping_revenue": ("shipping_revenue", "customer_receivable"),
            "reverse_cod_receivable": ("customer_receivable", "carrier_cod_receivable"),
            "recognize_return_cost": ("return_shipping_expense", "carrier_payable"),
        }
        already_settled = db.scalar(select(ShippingShipmentSettlement.id).where(ShippingShipmentSettlement.shipment_id == shipment.id,
            ShippingShipmentSettlement.batch_id.in_(select(ShippingSettlementBatch.id).where(ShippingSettlementBatch.company_id == shipment.company_id)),
        )) is not None
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
        if events:
            if user_id is None:
                raise ValueError("User identity is required to post shipping financial events")
            for event in events:
                shipping_accounting_service.post_financial_event(db, event_id=event.id, user_id=user_id)
        db.flush()
        return events


shipping_status_service = ShippingStatusService()
