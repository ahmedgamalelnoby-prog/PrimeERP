from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.shipping.models import ShippingCarrier
from app.modules.shipping.pricing_models import ShippingPricingProfile, ShippingPricingRule
from app.modules.shipping.pricing_schemas import ShippingCostInput, ShippingCostResponse


CENT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def _matches(rule: ShippingPricingRule, value: Decimal, zone_code: str | None) -> bool:
    if rule.zone_code and rule.zone_code != zone_code:
        return False
    if rule.min_value is not None and value < Decimal(rule.min_value):
        return False
    if rule.max_value is not None and value > Decimal(rule.max_value):
        return False
    return True


def _rule_amount(rule: ShippingPricingRule, value: Decimal, percentage_basis: Decimal) -> Decimal:
    included = Decimal(rule.included_units or 0)
    billable_units = max(value - included, Decimal("0"))
    amount = Decimal(rule.fixed_amount or 0) + billable_units * Decimal(rule.unit_amount or 0)
    amount += percentage_basis * Decimal(rule.percent_rate or 0) / Decimal("100")
    if rule.minimum_amount is not None:
        amount = max(amount, Decimal(rule.minimum_amount))
    return money(amount)


class ShippingPricingService:
    def calculate(self, db: Session, payload: ShippingCostInput) -> ShippingCostResponse:
        carrier = db.scalar(select(ShippingCarrier).where(
            ShippingCarrier.id == payload.carrier_id,
            ShippingCarrier.company_id == payload.company_id,
            ShippingCarrier.is_active.is_(True),
        ))
        if carrier is None:
            raise ValueError("Carrier does not belong to the company or is inactive")

        profile = db.scalar(
            select(ShippingPricingProfile)
            .where(
                ShippingPricingProfile.company_id == payload.company_id,
                ShippingPricingProfile.carrier_id == payload.carrier_id,
                ShippingPricingProfile.is_active.is_(True),
                ShippingPricingProfile.effective_from <= payload.calculation_date,
                (ShippingPricingProfile.effective_to.is_(None) | (ShippingPricingProfile.effective_to >= payload.calculation_date)),
            )
            .order_by(ShippingPricingProfile.priority.asc(), ShippingPricingProfile.effective_from.desc(), ShippingPricingProfile.id.desc())
        )
        if profile is None:
            raise ValueError("No active pricing profile applies to the calculation date")

        rules = db.scalars(
            select(ShippingPricingRule)
            .where(ShippingPricingRule.profile_id == profile.id, ShippingPricingRule.is_active.is_(True))
            .order_by(ShippingPricingRule.priority.asc(), ShippingPricingRule.id.asc())
        ).all()

        totals = {
            "base_shipping": Decimal("0"), "cod_fee": Decimal("0"), "cod_collected_fee": Decimal("0"),
            "card_fee": Decimal("0"), "surcharge_remote": Decimal("0"), "surcharge_rto": Decimal("0"),
            "surcharge_exchange": Decimal("0"), "storage_fee": Decimal("0"), "other_fees": Decimal("0"),
            "minimum_adjustment": Decimal("0"),
        }
        breakdown = []

        bases = {
            "base": (Decimal("1"), payload.order_value),
            "zone": (Decimal("1"), payload.order_value),
            "weight": (payload.weight_kg, Decimal("0")),
            "pieces": (payload.pieces, Decimal("0")),
            "order_value": (payload.order_value, payload.order_value),
            "tier": (payload.pieces, payload.order_value),
            "cod": (payload.cod_amount, payload.cod_amount),
            "cod_collected": (payload.cod_collected, payload.cod_collected),
            "card": (payload.card_amount, payload.card_amount),
            "minimum": (payload.order_value, payload.order_value),
            "remote": (Decimal("1") if payload.remote_area else Decimal("0"), payload.order_value),
            "rto": (Decimal("1") if payload.shipment_status == "returned" else Decimal("0"), payload.order_value),
            "exchange": (Decimal("1") if payload.shipment_status == "returned" else Decimal("0"), payload.order_value),
            "storage": (payload.storage_days, Decimal("0")),
        }

        for rule in rules:
            value, percentage_basis = bases[rule.rule_type]
            if rule.rule_type == "zone":
                if not rule.zone_code or rule.zone_code != payload.zone_code:
                    continue
                value = Decimal("1")
            elif rule.rule_type in {"remote", "rto", "exchange"} and value == 0:
                continue
            elif rule.rule_type == "card" and payload.card_amount <= 0:
                continue
            elif rule.rule_type in {"cod", "cod_collected"} and value <= 0:
                continue
            if not _matches(rule, value, payload.zone_code):
                continue

            if rule.rule_type == "minimum":
                continue
            amount = _rule_amount(rule, value, percentage_basis)
            if rule.rule_type == "base":
                totals["base_shipping"] += amount
            elif rule.rule_type == "cod":
                totals["cod_fee"] += amount
            elif rule.rule_type == "cod_collected":
                totals["cod_collected_fee"] += amount
            elif rule.rule_type == "card":
                totals["card_fee"] += amount
            elif rule.rule_type == "remote":
                totals["surcharge_remote"] += amount
            elif rule.rule_type == "rto":
                totals["surcharge_rto"] += amount
            elif rule.rule_type == "exchange":
                totals["surcharge_exchange"] += amount
            elif rule.rule_type == "storage":
                totals["storage_fee"] += amount
            elif rule.rule_type == "minimum":
                totals["minimum_adjustment"] += amount
            else:
                totals["other_fees"] += amount

            if amount:
                breakdown.append({"rule_id": rule.id, "rule_type": rule.rule_type, "description": rule.description, "amount": str(amount)})

        subtotal_before_minimum = sum(totals.values(), Decimal("0"))
        min_rules = [r for r in rules if r.rule_type == "minimum" and (not r.zone_code or r.zone_code == payload.zone_code)]
        if min_rules:
            floor = max((Decimal(r.minimum_amount or 0) for r in min_rules), default=Decimal("0"))
            if floor > 0 and subtotal_before_minimum < floor:
                adjustment = floor - subtotal_before_minimum
                totals["minimum_adjustment"] = money(adjustment)
                breakdown.append({"rule_id": None, "rule_type": "minimum_floor", "description": "Minimum charge adjustment", "amount": str(money(adjustment))})

        for key in totals:
            totals[key] = money(totals[key])
        total = money(sum(totals.values(), Decimal("0")))

        return ShippingCostResponse(
            profile_id=profile.id, profile_name=profile.name,
            **totals, total_cost=total, breakdown=breakdown,
        )


shipping_pricing_service = ShippingPricingService()
