from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.accounting.compliance_controls import validate_double_entry, validate_source
from app.modules.accounting.fiscal_years.services.fiscal_year_service import fiscal_year_service
from app.modules.accounting.journals.models import JournalEntry, AccountingJournal
from app.modules.accounting.journals.services.journal_service import journal_service
from app.modules.accounting.fiscal_years.models import AccountingPeriod, FiscalYear
from app.modules.commerce.accounting_models import CommerceAccountingSettings
from app.modules.companies.models import Company
from app.modules.rentals.models import RentalCharge

class RentalAccountingService:
    def post_charge(self, db: Session, charge: RentalCharge, user_id: int):
        company = db.scalar(select(Company).where(Company.id == charge.company_id, Company.tenant_id == charge.tenant_id))
        if company is None:
            raise HTTPException(409, "Rental charge company context is invalid")
        existing = db.scalar(select(JournalEntry).where(
            JournalEntry.tenant_id == charge.tenant_id, JournalEntry.company_id == charge.company_id,
            JournalEntry.source_module == "rentals", JournalEntry.source_entity == "rental_charge",
            JournalEntry.source_id == charge.id).with_for_update())
        if existing:
            charge.status = "posted"
            return existing
        settings = db.scalar(select(CommerceAccountingSettings).where(CommerceAccountingSettings.company_id == charge.company_id))
        if settings is None:
            raise HTTPException(409, "Commerce accounting configuration is required for rental posting")
        fiscal_year_service.assert_open_for_date(db, company_id=charge.company_id, posting_date=charge.charge_date)
        base=Decimal(charge.base_amount or 0); maintenance=Decimal(charge.maintenance_amount or 0)
        vat=Decimal(charge.vat_amount or 0); wht=Decimal(charge.wht_amount or 0); total=Decimal(charge.total_amount or 0)
        lines=[{"account_combination_id":settings.ar_account_id,"debit":total,"credit":0,"description":f"Rental charge {charge.id}"},
               {"account_combination_id":settings.sales_account_id,"debit":0,"credit":base+maintenance,"description":f"Rental revenue {charge.id}"}]
        if vat: lines.append({"account_combination_id":settings.output_vat_account_id,"debit":0,"credit":vat,"description":f"Rental VAT {charge.id}"})
        if wht:
            if settings.wht_account_id is None: raise HTTPException(409,"WHT account is required for rental charge posting")
            lines.append({"account_combination_id":settings.wht_account_id,"debit":wht,"credit":0,"description":f"Rental WHT {charge.id}"})
        validate_double_entry(lines); validate_source(source_module="rentals",source_entity="rental_charge",source_id=charge.id)
        journal=db.scalar(select(AccountingJournal).where(AccountingJournal.id==settings.sales_journal_id,AccountingJournal.company_id==charge.company_id,AccountingJournal.tenant_id==charge.tenant_id,AccountingJournal.is_active.is_(True)))
        if journal is None: raise HTTPException(409,"Configured sales journal was not found")
        period=db.scalar(select(AccountingPeriod).where(AccountingPeriod.company_id==charge.company_id,AccountingPeriod.tenant_id==charge.tenant_id,AccountingPeriod.start_date<=charge.charge_date,AccountingPeriod.end_date>=charge.charge_date,AccountingPeriod.status=="open",AccountingPeriod.allow_posting.is_(True)))
        if period is None: raise HTTPException(409,"No open posting period exists for the rental charge date")
        fy=db.scalar(select(FiscalYear).where(FiscalYear.id==period.fiscal_year_id,FiscalYear.company_id==charge.company_id,FiscalYear.tenant_id==charge.tenant_id))
        if fy is None: raise HTTPException(409,"Fiscal year for rental posting was not found")
        entry=journal_service.create_draft(db,tenant_id=charge.tenant_id,company_id=charge.company_id,branch_id=settings.default_branch_id,journal_id=journal.id,fiscal_year_id=fy.id,period_id=period.id,entry_number=f"RENT-{charge.id}",entry_date=charge.charge_date,description=f"Rental charge {charge.id}",lines=lines,user_id=user_id,source_module="rentals",source_entity="rental_charge",source_id=charge.id,commit=False)
        journal_service.submit(db,tenant_id=charge.tenant_id,entry_id=entry.id,user_id=user_id,commit=False)
        if journal.requires_approval:
            # Approval must be performed by a second authorized user.
            charge.status="pending"
        elif settings.auto_post and journal.auto_post:
            journal_service.post(db,tenant_id=charge.tenant_id,entry_id=entry.id,user_id=user_id,commit=False)
            charge.status="posted"
        else:
            charge.status="approved"
        db.flush(); return entry
rental_accounting_service=RentalAccountingService()
