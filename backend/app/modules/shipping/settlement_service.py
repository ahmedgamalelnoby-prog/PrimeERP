from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.shipping.models import ShippingCarrier, Shipment
from app.modules.shipping.cost_models import ShippingShipmentCost
from app.modules.shipping.settlement_models import ShippingSettlementBatch, ShippingShipmentSettlement
from app.modules.shipping.settlement_schemas import SettlementBatchCreate
from app.modules.shipping.status_models import ShippingFinancialEvent


class ShippingSettlementService:
    def create_batch(self, db: Session, payload: SettlementBatchCreate) -> ShippingSettlementBatch:
        existing = db.scalar(select(ShippingSettlementBatch).where(
            ShippingSettlementBatch.company_id == payload.company_id,
            ShippingSettlementBatch.reference == payload.reference.strip(),
        ))
        if existing:
            raise ValueError("Settlement reference already exists")

        carrier = db.scalar(select(ShippingCarrier).where(
            ShippingCarrier.id == payload.carrier_id,
            ShippingCarrier.company_id == payload.company_id,
            ShippingCarrier.is_active.is_(True),
        ))
        if carrier is None:
            raise ValueError("Carrier does not belong to the company or is inactive")

        ids = [line.shipment_id for line in payload.lines]
        if len(ids) != len(set(ids)):
            raise ValueError("A shipment can appear only once in a settlement batch")

        shipments = db.scalars(select(Shipment).where(
            Shipment.id.in_(ids),
            Shipment.company_id == payload.company_id,
            Shipment.carrier_id == payload.carrier_id,
        ).with_for_update()).all()
        by_id = {shipment.id: shipment for shipment in shipments}
        if len(by_id) != len(ids):
            raise ValueError("One or more shipments are invalid for this company/carrier")

        batch = ShippingSettlementBatch(
            company_id=payload.company_id,
            carrier_id=payload.carrier_id,
            reference=payload.reference.strip(),
            settlement_date=payload.settlement_date,
            notes=payload.notes,
        )
        db.add(batch)
        db.flush()

        gross = Decimal("0")
        fees = Decimal("0")
        fully_reconciled = True
        for line in payload.lines:
            shipment = by_id[line.shipment_id]
            if shipment.status != "delivered":
                raise ValueError(f"Shipment {shipment.id} must be delivered before COD settlement")
            if db.scalar(select(ShippingShipmentSettlement.id).where(ShippingShipmentSettlement.shipment_id == shipment.id)):
                raise ValueError(f"Shipment {shipment.id} is already settled")
            expected = Decimal(shipment.cod_amount or 0)
            collected = Decimal(line.collected_amount)
            breakdown_fee = Decimal(line.cod_commission) + Decimal(line.withdrawal_fee) + Decimal(line.other_fee)
            declared_fee = Decimal(line.carrier_fee)
            if declared_fee > 0 and breakdown_fee > 0 and declared_fee != breakdown_fee:
                raise ValueError(f"Carrier fee breakdown must equal carrier_fee for shipment {shipment.id}")
            fee = breakdown_fee if breakdown_fee > 0 else declared_fee
            if fee > collected:
                raise ValueError(f"Carrier fee cannot exceed collected amount for shipment {shipment.id}")
            net = collected - fee
            variance = collected - expected
            fully_reconciled = fully_reconciled and variance == 0
            gross += collected
            fees += fee

            # Settlement is the source of truth for the actual carrier fee
            # breakdown. Pricing at delivery is an estimate, so only the
            # delta is posted here; this prevents double-recognizing fees
            # while still capturing actual COD/withdrawal/other charges.
            estimated_cod_fee = Decimal("0")
            estimated_withdrawal_fee = Decimal("0")
            cost = db.scalar(select(ShippingShipmentCost).where(
                ShippingShipmentCost.shipment_id == shipment.id
            ))
            if cost is not None:
                estimated_cod_fee = Decimal(cost.cod_fee or 0) + Decimal(cost.cod_collected_fee or 0)
                estimated_withdrawal_fee = Decimal(cost.card_fee or 0)

            actual_fee_parts = {
                "cod_commission": Decimal(line.cod_commission),
                "withdrawal_fee": Decimal(line.withdrawal_fee),
                "other_fee": Decimal(line.other_fee),
            }
            estimated_fee_parts = {
                "cod_commission": estimated_cod_fee,
                "withdrawal_fee": estimated_withdrawal_fee,
                "other_fee": Decimal("0"),
            }
            for fee_key, actual_part in actual_fee_parts.items():
                delta = actual_part - estimated_fee_parts[fee_key]
                if delta == 0:
                    continue
                if delta > 0:
                    debit_role, credit_role = (
                        "cod_commission_expense" if fee_key == "cod_commission"
                        else "payment_withdrawal_fee_expense" if fee_key == "withdrawal_fee"
                        else "shipping_other_fee_expense",
                        "carrier_payable",
                    )
                else:
                    debit_role, credit_role = (
                        "carrier_payable",
                        "cod_commission_expense" if fee_key == "cod_commission"
                        else "payment_withdrawal_fee_expense" if fee_key == "withdrawal_fee"
                        else "shipping_other_fee_expense",
                    )
                db.add(ShippingFinancialEvent(
                    company_id=payload.company_id, carrier_id=payload.carrier_id, shipment_id=shipment.id,
                    event_key=f"settlement_fee_adjustment:{payload.reference}:{fee_key}",
                    event_type="settlement_fee_adjustment", event_date=payload.settlement_date,
                    amount=abs(delta), debit_role=debit_role, credit_role=credit_role,
                    source_status=shipment.status,
                    is_reversal=delta < 0,
                    description=f"Carrier settlement fee adjustment: {fee_key}",
                ))

            db.add(ShippingFinancialEvent(
                company_id=payload.company_id, carrier_id=payload.carrier_id, shipment_id=shipment.id,
                event_key=f"settlement:{payload.reference}", event_type="carrier_remittance", event_date=payload.settlement_date,
                amount=net, debit_role="bank_cash", credit_role="carrier_cod_receivable", source_status=shipment.status,
                description=f"Carrier remittance {payload.reference}",
            ))
            db.add(ShippingShipmentSettlement(
                batch_id=batch.id,
                shipment_id=shipment.id,
                expected_amount=expected,
                collected_amount=collected,
                carrier_fee=fee,
                cod_commission=Decimal(line.cod_commission),
                withdrawal_fee=Decimal(line.withdrawal_fee),
                other_fee=Decimal(line.other_fee),
                net_amount=net,
                variance=variance,
                reconciled=(variance == 0),
            ))

        batch.gross_amount = gross
        batch.carrier_fees = fees
        batch.net_amount = gross - fees
        batch.status = "reconciled" if fully_reconciled else "open"
        db.flush()
        return batch


shipping_settlement_service = ShippingSettlementService()
