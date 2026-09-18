from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.shipping.models import ShippingCarrier, Shipment
from app.modules.shipping.settlement_models import ShippingSettlementBatch, ShippingShipmentSettlement
from app.modules.shipping.settlement_schemas import SettlementBatchCreate


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
            fee = Decimal(line.carrier_fee)
            if fee > collected:
                raise ValueError(f"Carrier fee cannot exceed collected amount for shipment {shipment.id}")
            net = collected - fee
            variance = collected - expected
            fully_reconciled = fully_reconciled and variance == 0
            gross += collected
            fees += fee
            db.add(ShippingShipmentSettlement(
                batch_id=batch.id,
                shipment_id=shipment.id,
                expected_amount=expected,
                collected_amount=collected,
                carrier_fee=fee,
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
