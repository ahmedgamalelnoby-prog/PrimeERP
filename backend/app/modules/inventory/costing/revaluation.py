from __future__ import annotations
from datetime import date
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.accounting.fiscal_years.services.fiscal_year_service import fiscal_year_service
from app.modules.accounting.journals.models import AccountingJournal
from app.modules.accounting.journals.services.journal_service import journal_service
from app.modules.companies.models import Company
from app.modules.inventory.items.models import InventoryItem, InventoryStock
from app.modules.inventory.stock_moves.models import InventoryAccountingConfig
from app.modules.inventory.costing.revaluation_models import InventoryCostRevaluation

class InventoryCostRevaluationService:
    def create(self, db: Session, *, tenant_id: int, user_id: int, company_id: int, item_id: int, warehouse_id: int, new_unit_cost: Decimal, effective_date: date, reason: str):
        company=db.scalar(select(Company).where(Company.id==company_id,Company.tenant_id==tenant_id))
        if not company: raise ValueError("Company is outside the current tenant")
        fiscal_year_service.assert_open_for_date(db, tenant_id=tenant_id, company_id=company_id, posting_date=effective_date)
        item=db.scalar(select(InventoryItem).where(InventoryItem.id==item_id,InventoryItem.company_id==company_id,InventoryItem.is_active.is_(True)))
        stock=db.scalar(select(InventoryStock).where(InventoryStock.company_id==company_id,InventoryStock.item_id==item_id,InventoryStock.warehouse_id==warehouse_id,InventoryStock.variant_id.is_(None)).with_for_update())
        if not item or not stock: raise ValueError("Item or warehouse stock was not found")
        old=Decimal(stock.average_cost or 0); qty=Decimal(stock.quantity_on_hand or 0)
        if new_unit_cost < 0 or qty < 0: raise ValueError("Invalid revaluation values")
        delta=(new_unit_cost-old)*qty
        if delta==0: raise ValueError("Revaluation has no financial impact")
        row=InventoryCostRevaluation(company_id=company_id,item_id=item_id,warehouse_id=warehouse_id,effective_date=effective_date,old_unit_cost=old,new_unit_cost=new_unit_cost,quantity=qty,delta_value=delta,reason=reason,status="draft",created_by=user_id)
        db.add(row); db.flush(); return row
    def post(self, db: Session, *, tenant_id:int,user_id:int,revaluation_id:int):
        row=db.scalar(select(InventoryCostRevaluation).where(InventoryCostRevaluation.id==revaluation_id).with_for_update())
        if not row: raise ValueError("Revaluation not found")
        if row.status=="posted": return row
        if row.status!="draft": raise ValueError("Only draft revaluations can be posted")
        period=fiscal_year_service.assert_open_for_date(db,tenant_id=tenant_id,company_id=row.company_id,posting_date=row.effective_date)
        config=db.scalar(select(InventoryAccountingConfig).where(InventoryAccountingConfig.company_id==row.company_id,InventoryAccountingConfig.tenant_id==tenant_id,InventoryAccountingConfig.is_active=="Y"))
        if not config: raise ValueError("Inventory accounting configuration is missing")
        journal=db.scalar(select(AccountingJournal).where(AccountingJournal.id==config.journal_id,AccountingJournal.company_id==row.company_id,AccountingJournal.tenant_id==tenant_id,AccountingJournal.is_active.is_(True)))
        if not journal: raise ValueError("Inventory journal is missing")
        amount=abs(Decimal(row.delta_value))
        if row.delta_value>0:
            lines=[{"account_combination_id":config.inventory_account_id,"debit":amount,"credit":0,"description":f"Inventory revaluation {row.id}"},{"account_combination_id":config.adjustment_account_id,"debit":0,"credit":amount,"description":f"Inventory revaluation {row.id}"}]
        else:
            lines=[{"account_combination_id":config.adjustment_account_id,"debit":amount,"credit":0,"description":f"Inventory revaluation {row.id}"},{"account_combination_id":config.inventory_account_id,"debit":0,"credit":amount,"description":f"Inventory revaluation {row.id}"}]
        entry=journal_service.create_draft(db,tenant_id=tenant_id,company_id=row.company_id,branch_id=config.branch_id,journal_id=journal.id,fiscal_year_id=period.fiscal_year_id,period_id=period.id,entry_number=f"INV-REVAL-{row.id}",entry_date=row.effective_date,description=row.reason,lines=lines,user_id=user_id,source_module="inventory",source_entity="cost_revaluation",source_id=row.id,commit=False)
        journal_service.submit(db,tenant_id=tenant_id,entry_id=entry.id,user_id=user_id,commit=False)
        if journal.requires_approval: journal_service.approve(db,tenant_id=tenant_id,entry_id=entry.id,user_id=user_id,commit=False)
        if journal.auto_post: journal_service.post(db,tenant_id=tenant_id,entry_id=entry.id,user_id=user_id,commit=False)
        stock=db.scalar(select(InventoryStock).where(InventoryStock.company_id==row.company_id,InventoryStock.item_id==row.item_id,InventoryStock.warehouse_id==row.warehouse_id,InventoryStock.variant_id.is_(None)).with_for_update())
        if stock: stock.average_cost=row.new_unit_cost
        row.journal_entry_id=entry.id; row.status="posted"; row.posted_by=user_id
        return row
inventory_cost_revaluation_service=InventoryCostRevaluationService()
