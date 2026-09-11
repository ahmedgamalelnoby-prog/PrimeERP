from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounting.journals.models import AccountingJournal
from app.modules.accounting.journals.services.journal_service import journal_service
from app.modules.companies.models import Company
from app.modules.shipping.models import ShippingCarrier, Shipment
from app.modules.shipping.settlement_models import ShippingSettlementBatch, ShippingShipmentSettlement
from app.modules.shipping.settlement_schemas import SettlementBatchCreate


class ShippingSettlementService:
    def create_batch(self, db: Session, payload: SettlementBatchCreate, user_id: int) -> ShippingSettlementBatch:
        company = db.scalar(select(Company).where(Company.id == payload.company_id, Company.is_active.is_(True)))
        if company is None:
            raise HTTPException(403, "Company is inactive or not found")
        existing = db.scalar(select(ShippingSettlementBatch).where(ShippingSettlementBatch.company_id == payload.company_id, ShippingSettlementBatch.reference == payload.reference.strip()))
        if existing:
            raise HTTPException(409, "Settlement reference already exists")
        carrier = db.scalar(select(ShippingCarrier).where(ShippingCarrier.id == payload.carrier_id, ShippingCarrier.company_id == payload.company_id, ShippingCarrier.is_active.is_(True)))
        if carrier is None:
            raise HTTPException(409, "Carrier does not belong to the company or is inactive")
        if not all((carrier.settlement_account_id, carrier.cash_account_id, carrier.fee_account_id, carrier.settlement_journal_id, carrier.branch_id)):
            raise HTTPException(409, "Carrier accounting settlement configuration is incomplete")
        journal = db.scalar(select(AccountingJournal).where(AccountingJournal.id == carrier.settlement_journal_id, AccountingJournal.company_id == payload.company_id, AccountingJournal.tenant_id == company.tenant_id, AccountingJournal.is_active.is_(True)))
        if journal is None:
            raise HTTPException(409, "Carrier settlement journal is invalid for the company")

        ids = [line.shipment_id for line in payload.lines]
        if len(ids) != len(set(ids)):
            raise HTTPException(422, "A shipment can appear only once in a settlement batch")
        shipments = db.scalars(select(Shipment).where(Shipment.id.in_(ids), Shipment.company_id == payload.company_id, Shipment.carrier_id == payload.carrier_id).with_for_update()).all()
        by_id = {shipment.id: shipment for shipment in shipments}
        if len(by_id) != len(ids):
            raise HTTPException(422, "One or more shipments are invalid for this company/carrier")

        batch = ShippingSettlementBatch(company_id=payload.company_id, carrier_id=payload.carrier_id, reference=payload.reference.strip(), settlement_date=payload.settlement_date, notes=payload.notes)
        db.add(batch); db.flush()
        gross = Decimal("0"); fees = Decimal("0"); fully_reconciled = True
        for line in payload.lines:
            shipment = by_id[line.shipment_id]
            if shipment.status not in {"delivered", "returned"}:
                raise HTTPException(409, f"Shipment {shipment.id} is not eligible for settlement")
            if db.scalar(select(ShippingShipmentSettlement.id).where(ShippingShipmentSettlement.shipment_id == shipment.id)):
                raise HTTPException(409, f"Shipment {shipment.id} is already settled")
            expected = Decimal(shipment.cod_amount or 0); collected = Decimal(line.collected_amount); fee = Decimal(line.carrier_fee)
            if fee > collected:
                raise HTTPException(422, f"Carrier fee cannot exceed collected amount for shipment {shipment.id}")
            variance = collected - expected
            fully_reconciled = fully_reconciled and variance == 0
            gross += collected; fees += fee
            db.add(ShippingShipmentSettlement(batch_id=batch.id, shipment_id=shipment.id, expected_amount=expected, collected_amount=collected, carrier_fee=fee, net_amount=collected - fee, variance=variance, reconciled=(variance == 0)))

        batch.gross_amount = gross; batch.carrier_fees = fees; batch.net_amount = gross - fees; batch.status = "reconciled" if fully_reconciled else "open"
        db.flush()

        journal_service._active_company(db, company.tenant_id, payload.company_id)
        entry = journal_service.create_draft(
            db, tenant_id=company.tenant_id, company_id=payload.company_id, branch_id=carrier.branch_id,
            journal_id=carrier.settlement_journal_id, fiscal_year_id=0, period_id=0,
            entry_number=f"SHIP-SET-{batch.id}", entry_date=payload.settlement_date,
            description=f"Shipping settlement {payload.reference}", user_id=user_id,
            source_module="shipping", source_entity="shipping_settlement", source_id=batch.id,
            lines=[
                {"account_combination_id": carrier.cash_account_id, "debit": batch.net_amount, "credit": 0, "description": f"Carrier settlement cash {payload.reference}"},
                {"account_combination_id": carrier.fee_account_id, "debit": batch.carrier_fees, "credit": 0, "description": f"Carrier fees {payload.reference}"},
                {"account_combination_id": carrier.settlement_account_id, "debit": 0, "credit": batch.gross_amount, "description": f"Carrier clearing {payload.reference}"},
            ], commit=False,
        )
        journal_service.submit(db, tenant_id=company.tenant_id, entry_id=entry.id, user_id=user_id, commit=False)
        if journal.requires_approval:
            journal_service.approve(db, tenant_id=company.tenant_id, entry_id=entry.id, user_id=user_id, commit=False)
        if journal.auto_post:
            journal_service.post(db, tenant_id=company.tenant_id, entry_id=entry.id, user_id=user_id, commit=False)
        db.flush()
        return batch


shipping_settlement_service = ShippingSettlementService()
