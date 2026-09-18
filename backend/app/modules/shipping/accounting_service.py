from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounting.fiscal_years.models import AccountingPeriod, FiscalYear
from app.modules.accounting.journals.models import AccountingJournal, JournalEntry
from app.modules.accounting.journals.services.journal_service import journal_service
from app.modules.branches.models import Branch
from app.modules.companies.models import Company
from app.modules.commerce.accounting_models import CommerceAccountingSettings
from app.modules.shipping.models import ShippingCarrier
from app.modules.shipping.settlement_models import ShippingSettlementBatch, ShippingShipmentSettlement
from app.modules.shipping.status_models import ShippingFinancialEvent


class ShippingAccountingService:
    def post_settlement(self, db: Session, *, batch_id: int, user_id: int, posting_date: date | None = None) -> JournalEntry:
        """Compatibility entry point: post the batch's already-created financial events.

        Settlement itself creates a remittance event and fee adjustments. Those events
        are the accounting source of truth, so this method never creates a second
        aggregate journal that could double-post the same cash movement.
        """
        batch = db.scalar(select(ShippingSettlementBatch).where(
            ShippingSettlementBatch.id == batch_id
        ).with_for_update())
        if batch is None:
            raise HTTPException(status_code=404, detail="Settlement batch not found")

        shipment_ids = list(db.scalars(select(ShippingShipmentSettlement.shipment_id).where(
            ShippingShipmentSettlement.batch_id == batch.id
        )).all())
        if not shipment_ids:
            raise HTTPException(status_code=409, detail="Settlement batch has no shipment lines")

        events = list(db.scalars(select(ShippingFinancialEvent).where(
            ShippingFinancialEvent.company_id == batch.company_id,
            ShippingFinancialEvent.carrier_id == batch.carrier_id,
            ShippingFinancialEvent.shipment_id.in_(shipment_ids),
            ShippingFinancialEvent.event_type.in_({"carrier_remittance", "settlement_fee_adjustment"}),
        ).order_by(ShippingFinancialEvent.id)).all())
        if not events:
            raise HTTPException(status_code=409, detail="Settlement has no financial events to post")

        last_entry = None
        for event in events:
            last_entry = self.post_financial_event(db, event_id=event.id, user_id=user_id)
        db.flush()
        return last_entry

    def post_financial_event(self, db: Session, *, event_id: int, user_id: int) -> JournalEntry:
        event = db.scalar(select(ShippingFinancialEvent).where(ShippingFinancialEvent.id == event_id).with_for_update())
        if event is None:
            raise HTTPException(status_code=404, detail="Shipping financial event not found")

        company = db.get(Company, event.company_id)
        if company is None:
            raise HTTPException(status_code=404, detail="Company not found")

        existing = db.scalar(select(JournalEntry).where(
            JournalEntry.tenant_id == company.tenant_id,
            JournalEntry.company_id == event.company_id,
            JournalEntry.source_module == "shipping",
            JournalEntry.source_entity == "financial_event",
            JournalEntry.source_id == event.id,
        ))
        if existing is not None:
            return existing

        carrier = db.scalar(select(ShippingCarrier).where(
            ShippingCarrier.id == event.carrier_id,
            ShippingCarrier.company_id == event.company_id,
            ShippingCarrier.is_active.is_(True),
        ))
        if carrier is None or not all((carrier.settlement_account_id, carrier.cash_account_id, carrier.fee_account_id, carrier.settlement_journal_id, carrier.branch_id)):
            raise HTTPException(status_code=409, detail="Carrier shipping-accounting configuration is incomplete")

        branch = db.scalar(select(Branch).where(
            Branch.id == carrier.branch_id,
            Branch.company_id == company.id,
            Branch.tenant_id == company.tenant_id,
            Branch.is_active.is_(True),
        ))
        journal = db.scalar(select(AccountingJournal).where(
            AccountingJournal.id == carrier.settlement_journal_id,
            AccountingJournal.company_id == company.id,
            AccountingJournal.tenant_id == company.tenant_id,
            AccountingJournal.is_active.is_(True),
        ))
        settings = db.scalar(select(CommerceAccountingSettings).where(CommerceAccountingSettings.company_id == company.id))
        if branch is None or journal is None:
            raise HTTPException(status_code=409, detail="Carrier shipping journal or branch is invalid")
        if settings is None:
            raise HTTPException(status_code=409, detail="Commerce accounting configuration is required for shipping AR/revenue posting")

        account_map = {
            "customer_receivable": settings.ar_account_id,
            "sales_revenue": settings.sales_account_id,
            "shipping_revenue": settings.sales_account_id,
            "shipping_expense": carrier.fee_account_id,
            "return_shipping_expense": carrier.fee_account_id,
            "cod_commission_expense": carrier.fee_account_id,
            "payment_withdrawal_fee_expense": carrier.fee_account_id,
            "shipping_other_fee_expense": carrier.fee_account_id,
            "carrier_payable": carrier.settlement_account_id,
            "carrier_cod_receivable": carrier.settlement_account_id,
            "bank_cash": carrier.cash_account_id,
        }
        debit_account = account_map.get(event.debit_role)
        credit_account = account_map.get(event.credit_role)
        if debit_account is None or credit_account is None:
            raise HTTPException(status_code=409, detail=f"Unsupported shipping accounting role: {event.debit_role}/{event.credit_role}")

        entry_date = event.event_date
        period = db.scalar(select(AccountingPeriod).where(
            AccountingPeriod.company_id == company.id,
            AccountingPeriod.tenant_id == company.tenant_id,
            AccountingPeriod.start_date <= entry_date,
            AccountingPeriod.end_date >= entry_date,
            AccountingPeriod.status == "open",
            AccountingPeriod.allow_posting.is_(True),
        ).order_by(AccountingPeriod.period_number.desc()))
        if period is None:
            raise HTTPException(status_code=409, detail="No open posting period exists for the shipping event date")
        fiscal_year = db.scalar(select(FiscalYear).where(
            FiscalYear.id == period.fiscal_year_id,
            FiscalYear.company_id == company.id,
            FiscalYear.tenant_id == company.tenant_id,
        ))
        if fiscal_year is None:
            raise HTTPException(status_code=409, detail="Fiscal year for shipping event was not found")

        amount = Decimal(event.amount or 0)
        if amount <= 0:
            raise HTTPException(status_code=422, detail="Shipping financial event amount must be positive")

        entry = journal_service.create_draft(
            db,
            tenant_id=company.tenant_id,
            company_id=company.id,
            branch_id=branch.id,
            journal_id=journal.id,
            fiscal_year_id=fiscal_year.id,
            period_id=period.id,
            entry_number=f"SHP-EVT-{event.id}",
            entry_date=entry_date,
            description=event.description or f"Shipping financial event {event.id}",
            lines=[
                {"account_combination_id": debit_account, "debit": amount, "credit": 0, "description": event.description},
                {"account_combination_id": credit_account, "debit": 0, "credit": amount, "description": event.description},
            ],
            user_id=user_id,
            source_module="shipping",
            source_entity="financial_event",
            source_id=event.id,
            commit=False,
        )
        journal_service.submit(db, tenant_id=company.tenant_id, entry_id=entry.id, user_id=user_id, commit=False)
        if journal.requires_approval:
            journal_service.approve(db, tenant_id=company.tenant_id, entry_id=entry.id, user_id=user_id, commit=False)
        if journal.auto_post:
            journal_service.post(db, tenant_id=company.tenant_id, entry_id=entry.id, user_id=user_id, commit=False)
        return entry


shipping_accounting_service = ShippingAccountingService()
