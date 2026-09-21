from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.modules.accounting.journals.models import AccountingJournal, JournalEntry
from app.modules.accounting.journals.services.journal_service import journal_service
from app.modules.accounting.fiscal_years.models import AccountingPeriod, FiscalYear
from app.modules.companies.models import Company
from app.modules.branches.models import Branch
from app.modules.catalog.models import Recipe, RecipeLine, ProductVariant
from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.stock_moves.schemas import StockMoveCreate
from app.modules.inventory.stock_moves.service import inventory_stock_move_service
from app.modules.inventory.stock_moves.models import InventoryAccountingConfig, InventoryStockMove
from app.modules.inventory.warehouses.models import InventoryWarehouse
from app.modules.commerce.accounting_models import CommerceAccountingSettings, POSPaymentAccountMapping
from app.modules.pos.models import POSOutlet, POSDevice, POSSession, POSOrder, POSOrderLine, POSPayment
from app.modules.identity.models.user import User


class POSService:
    def _company(self, db, cid, user):
        return db.scalar(select(Company).where(Company.id == cid, Company.tenant_id == user.tenant_id))

    def _payment_account(self, db, *, company_id, method):
        mapping = db.scalar(select(POSPaymentAccountMapping).where(POSPaymentAccountMapping.company_id == company_id, POSPaymentAccountMapping.method == method))
        if mapping:
            return mapping.account_combination_id
        settings = db.scalar(select(CommerceAccountingSettings).where(CommerceAccountingSettings.company_id == company_id))
        if not settings:
            raise ValueError("Commerce accounting configuration is required for POS")
        return settings.default_payment_account_id

    def create_outlet(self, db, p, user):
        c=self._company(db,p.company_id,user)
        if not c: raise ValueError("Company is outside the current tenant")
        b=db.scalar(select(Branch).where(Branch.id==p.branch_id,Branch.company_id==c.id,Branch.tenant_id==c.tenant_id,Branch.is_active.is_(True)))
        loc=db.scalar(select(InventoryLocation).join(InventoryWarehouse, InventoryWarehouse.id==InventoryLocation.warehouse_id).where(InventoryLocation.id==p.inventory_location_id,InventoryLocation.company_id==c.id,InventoryLocation.is_active.is_(True),InventoryLocation.is_virtual.is_(False),InventoryWarehouse.company_id==c.id,InventoryWarehouse.branch_id==b.id,InventoryWarehouse.is_active.is_(True)))
        if not b or not loc: raise ValueError("Branch or inventory location is invalid or belongs to another branch")
        o=POSOutlet(**p.model_dump());db.add(o);db.flush();return o

    def create_device(self, db, p, user):
        c=self._company(db,p.company_id,user)
        if not c: raise ValueError("Company is outside the current tenant")
        o=db.scalar(select(POSOutlet).where(POSOutlet.id==p.outlet_id,POSOutlet.company_id==c.id,POSOutlet.is_active.is_(True)))
        if not o: raise ValueError("Outlet is invalid")
        d=POSDevice(**p.model_dump());db.add(d);db.flush();return d

    def open_session(self, db, p, user):
        c=self._company(db,p.company_id,user)
        if not c: raise ValueError("Company is outside the current tenant")
        o=db.scalar(select(POSOutlet).where(POSOutlet.id==p.outlet_id,POSOutlet.company_id==c.id,POSOutlet.is_active.is_(True)))
        d=db.scalar(select(POSDevice).where(POSDevice.id==p.device_id,POSDevice.outlet_id==p.outlet_id,POSDevice.company_id==c.id,POSDevice.is_active.is_(True)))
        if not o or not d: raise ValueError("Outlet or device is invalid")
        cashier=db.scalar(select(User).where(User.id==p.cashier_user_id,User.tenant_id==c.tenant_id,User.is_active.is_(True),User.is_deleted.is_(False)))
        if not cashier: raise ValueError("Cashier is inactive, deleted, or outside the current tenant")
        existing=db.scalar(select(POSSession).where(POSSession.company_id==c.id,POSSession.device_id==d.id,POSSession.status=="open").with_for_update())
        if existing: raise ValueError("Device already has an open session")
        s=POSSession(**p.model_dump(),status="open");db.add(s);db.flush();return s

    def create_order(self, db, p, user):
        c=self._company(db,p.company_id,user)
        if not c: raise ValueError("Company is outside the current tenant")
        s=db.scalar(select(POSSession).where(POSSession.id==p.session_id,POSSession.company_id==c.id).with_for_update())
        if not s or s.status!="open": raise ValueError("Session is not open")
        if db.scalar(select(POSOrder).where(POSOrder.company_id==c.id,POSOrder.number==p.number)): raise ValueError("POS order number already exists")
        o=POSOrder(company_id=c.id,session_id=s.id,number=p.number);db.add(o);db.flush();sub=tax=Decimal("0")
        for x in p.lines:
            item=db.scalar(select(InventoryItem).where(InventoryItem.id==x.item_id,InventoryItem.company_id==c.id,InventoryItem.is_active.is_(True)))
            if not item: raise ValueError("Item is unavailable")
            if x.variant_id is not None:
                variant=db.scalar(select(ProductVariant).where(ProductVariant.id==x.variant_id,ProductVariant.company_id==c.id,ProductVariant.product_id==item.id,ProductVariant.is_active.is_(True)))
                if not variant: raise ValueError("Variant does not belong to the item/company or is inactive")
            elif db.scalar(select(ProductVariant.id).where(ProductVariant.company_id==c.id,ProductVariant.product_id==item.id,ProductVariant.is_active.is_(True)).limit(1)) is not None:
                raise ValueError("This item has active variants; POS order lines must identify the variant")
            recipe=db.scalar(select(Recipe).where(Recipe.company_id==c.id,Recipe.product_id==item.id,Recipe.is_active.is_(True)).order_by(Recipe.version.desc()).limit(1))
            ls=(x.quantity*x.unit_price).quantize(Decimal("0.0001"),ROUND_HALF_UP); lt=(ls*x.tax_percent/100).quantize(Decimal("0.0001"),ROUND_HALF_UP)
            db.add(POSOrderLine(order_id=o.id,item_id=item.id,variant_id=x.variant_id,quantity=x.quantity,unit_price=x.unit_price,tax_percent=x.tax_percent,line_subtotal=ls,line_tax=lt,line_total=ls+lt,recipe_id=recipe.id if recipe else None));sub+=ls;tax+=lt
        o.subtotal=sub;o.tax_total=tax;o.total=sub+tax;db.flush();return o

    def _accounting_context(self,db,cid,user,entry_date,branch_id=None):
        c=self._company(db,cid,user)
        if not c: raise ValueError("Company is outside the current tenant")
        settings=db.scalar(select(CommerceAccountingSettings).where(CommerceAccountingSettings.company_id==cid))
        if not settings: raise ValueError("Commerce accounting configuration is required for POS")
        target_branch_id = branch_id if branch_id is not None else settings.default_branch_id
        b=db.scalar(select(Branch).where(Branch.id==target_branch_id,Branch.company_id==cid,Branch.tenant_id==c.tenant_id,Branch.is_active.is_(True)))
        period=db.scalar(select(AccountingPeriod).where(AccountingPeriod.company_id==cid,AccountingPeriod.tenant_id==c.tenant_id,AccountingPeriod.start_date<=entry_date,AccountingPeriod.end_date>=entry_date,AccountingPeriod.status=="open",AccountingPeriod.allow_posting.is_(True)))
        fy=db.scalar(select(FiscalYear).where(FiscalYear.id==period.fiscal_year_id,FiscalYear.company_id==cid,FiscalYear.tenant_id==c.tenant_id)) if period else None
        journal=db.scalar(select(AccountingJournal).where(AccountingJournal.id==settings.sales_journal_id,AccountingJournal.company_id==cid,AccountingJournal.tenant_id==c.tenant_id,AccountingJournal.is_active.is_(True)))
        if not b or not period or not fy or not journal: raise ValueError("Configured accounting journal or fiscal year is unavailable")
        return c,settings,b,period,fy,journal

    def _post(self,db,*,cid,user,entry_number,description,lines,source_entity,source_id,journal=None,branch_id=None):
        c,settings,b,p,fy,j=self._accounting_context(db,cid,user,datetime.now(timezone.utc).date(),branch_id=branch_id)
        j=journal or j
        if not j.auto_post: raise ValueError("POS accounting journal must have auto-post enabled for atomic order finalization and payment settlement")
        existing=db.scalar(select(JournalEntry).where(JournalEntry.tenant_id==c.tenant_id,JournalEntry.company_id==cid,JournalEntry.source_module=="pos",JournalEntry.source_entity==source_entity,JournalEntry.source_id==source_id).with_for_update())
        if existing:return existing
        e=journal_service.create_draft(db,tenant_id=c.tenant_id,company_id=cid,branch_id=b.id,journal_id=j.id,fiscal_year_id=fy.id,period_id=p.id,entry_number=entry_number,entry_date=datetime.now(timezone.utc).date(),description=description,lines=lines,user_id=user.id,source_module="pos",source_entity=source_entity,source_id=source_id,commit=False)
        journal_service.submit(db,tenant_id=c.tenant_id,entry_id=e.id,user_id=user.id,commit=False)
        if j.requires_approval: journal_service.approve(db,tenant_id=c.tenant_id,entry_id=e.id,user_id=user.id,commit=False)
        if j.auto_post: journal_service.post(db,tenant_id=c.tenant_id,entry_id=e.id,user_id=user.id,commit=False)
        return e

    def finalize(self,db,cid,order_id,user):
        c=self._company(db,cid,user)
        o=db.scalar(select(POSOrder).where(POSOrder.id==order_id,POSOrder.company_id==cid).with_for_update())
        if not c or not o: raise ValueError("Order not found")
        if o.status=="finalized": return o
        if o.status!="draft": raise ValueError("Only draft orders can be finalized")
        s=db.scalar(select(POSSession).where(POSSession.id==o.session_id,POSSession.company_id==cid).with_for_update())
        outlet=db.scalar(select(POSOutlet).where(POSOutlet.id==s.outlet_id,POSOutlet.company_id==cid)) if s else None
        if not s or s.status!="open" or not outlet: raise ValueError("Session or outlet is invalid")
        for line in db.scalars(select(POSOrderLine).where(POSOrderLine.order_id==o.id)).all():
            recipe=db.scalar(select(Recipe).where(Recipe.id==line.recipe_id,Recipe.company_id==cid)) if line.recipe_id else None
            if recipe:
                ingredients=db.scalars(select(RecipeLine).where(RecipeLine.recipe_id==recipe.id).order_by(RecipeLine.line_no)).all()
                for rl in ingredients:
                    qty=(Decimal(line.quantity)*Decimal(rl.quantity)/Decimal(recipe.yield_quantity)).quantize(Decimal("0.000001"),ROUND_HALF_UP)
                    source_id=f"{line.id}:{rl.line_no}"
                    existing_move=db.scalar(select(InventoryStockMove).where(InventoryStockMove.company_id==cid,__import__("app.modules.inventory.stock_moves.models",fromlist=["InventoryStockMove"]).InventoryStockMove.source_module=="pos",__import__("app.modules.inventory.stock_moves.models",fromlist=["InventoryStockMove"]).InventoryStockMove.source_entity=="pos_order_line",__import__("app.modules.inventory.stock_moves.models",fromlist=["InventoryStockMove"]).InventoryStockMove.source_id==source_id))
                    if not existing_move:
                        move=StockMoveCreate(company_id=cid,item_id=rl.ingredient_product_id,variant_id=None,source_location_id=outlet.inventory_location_id,quantity=qty,unit_cost=0,movement_type="issue",source_module="pos",source_entity="pos_order_line",source_id=source_id,notes=f"POS recipe consumption {o.number}")
                        draft=inventory_stock_move_service.create_draft(db,move)
                        inventory_stock_move_service.post(db,tenant_id=c.tenant_id,company_id=cid,move_id=draft.id,user_id=user.id)
            else:
                source_id=str(line.id)
                existing_move=db.scalar(select(__import__("app.modules.inventory.stock_moves.models",fromlist=["InventoryStockMove"]).InventoryStockMove).where(__import__("app.modules.inventory.stock_moves.models",fromlist=["InventoryStockMove"]).InventoryStockMove.company_id==cid,__import__("app.modules.inventory.stock_moves.models",fromlist=["InventoryStockMove"]).InventoryStockMove.source_module=="pos",__import__("app.modules.inventory.stock_moves.models",fromlist=["InventoryStockMove"]).InventoryStockMove.source_entity=="pos_order_line",__import__("app.modules.inventory.stock_moves.models",fromlist=["InventoryStockMove"]).InventoryStockMove.source_id==source_id))
                if not existing_move:
                    move=StockMoveCreate(company_id=cid,item_id=line.item_id,variant_id=line.variant_id,source_location_id=outlet.inventory_location_id,quantity=line.quantity,unit_cost=0,movement_type="issue",source_module="pos",source_entity="pos_order_line",source_id=source_id,notes=f"POS stock consumption {o.number}")
                    draft=inventory_stock_move_service.create_draft(db,move)
                    inventory_stock_move_service.post(db,tenant_id=c.tenant_id,company_id=cid,move_id=draft.id,user_id=user.id)
        _,settings,_,_,_,_=self._accounting_context(db,cid,user,datetime.now(timezone.utc).date(),branch_id=outlet.branch_id)
        self._post(db, cid=cid, user=user, entry_number=f"POS-{o.id}", description=f"POS order {o.number}", source_entity="pos_order", source_id=o.id, lines=[
            {"account_combination_id": settings.ar_account_id, "debit": Decimal(o.total), "credit": 0, "description": f"POS AR {o.number}"},
            {"account_combination_id": settings.sales_account_id, "debit": 0, "credit": Decimal(o.subtotal), "description": f"POS sales {o.number}"},
            {"account_combination_id": settings.output_vat_account_id, "debit": 0, "credit": Decimal(o.tax_total), "description": f"POS VAT {o.number}"},
        ], branch_id=outlet.branch_id)
        o.status="finalized";o.finalized_at=datetime.now(timezone.utc);db.flush();return o

    def pay(self,db,p,user):
        c=self._company(db,p.company_id,user)
        if not c: raise ValueError("Company is outside the current tenant")
        o=db.scalar(select(POSOrder).where(POSOrder.id==p.order_id,POSOrder.company_id==c.id).with_for_update())
        if not o or o.status!="finalized": raise ValueError("Only finalized orders can receive payments")
        existing=db.scalar(select(POSPayment).where(POSPayment.company_id==c.id,POSPayment.idempotency_key==p.idempotency_key).with_for_update())
        if existing:return existing
        if p.method not in {"cash","card","bank","other"}:raise ValueError("Unsupported payment method")
        if Decimal(o.paid_total)+p.amount>Decimal(o.total):raise ValueError("Payment exceeds outstanding balance")
        session=db.scalar(select(POSSession).where(POSSession.id==o.session_id,POSSession.company_id==c.id))
        outlet=db.scalar(select(POSOutlet).where(POSOutlet.id==session.outlet_id,POSOutlet.company_id==c.id)) if session else None
        if not session or not outlet or session.status!="open": raise ValueError("Order session or outlet is invalid")
        settings=db.scalar(select(CommerceAccountingSettings).where(CommerceAccountingSettings.company_id==c.id))
        if not settings: raise ValueError("Commerce accounting configuration is required for POS")
        account=self._payment_account(db,company_id=c.id,method=p.method)
        entry=self._post(db,cid=c.id,user=user,entry_number=f"POS-PAY-{p.idempotency_key}",description=f"POS payment {o.number}",source_entity="pos_payment",source_id=p.idempotency_key,branch_id=outlet.branch_id,lines=[{"account_combination_id":account,"debit":p.amount,"credit":0,"description":f"{p.method} payment"},{"account_combination_id":settings.ar_account_id,"debit":0,"credit":p.amount,"description":f"POS AR settlement {o.number}"}])
        payment=POSPayment(company_id=c.id,order_id=o.id,method=p.method,amount=p.amount,idempotency_key=p.idempotency_key,accounting_entry_id=entry.id);db.add(payment);o.paid_total=Decimal(o.paid_total)+p.amount;db.flush();return payment

    def close_session(self,db,cid,sid,closing_total,user,closing_cash=None,closing_card=None,closing_bank=None,closing_other=None):
        s=db.scalar(select(POSSession).where(POSSession.id==sid,POSSession.company_id==cid).with_for_update())
        if not s or s.status!="open" or not self._company(db,cid,user):raise ValueError("Session is invalid or outside the tenant")
        unpaid=db.scalar(select(func.count()).select_from(POSOrder).where(POSOrder.session_id==sid,POSOrder.status=="finalized",POSOrder.paid_total<POSOrder.total))
        if unpaid:raise ValueError("Cannot close a session with unpaid finalized orders")
        payments=db.scalars(select(POSPayment).where(POSPayment.company_id==cid,POSPayment.order_id.in_(select(POSOrder.id).where(POSOrder.session_id==sid)),POSPayment.status=="posted")).all()
        expected={m:sum((Decimal(x.amount) for x in payments if x.method==m),Decimal("0")) for m in ("cash","card","bank","other")}
        expected_total=sum(expected.values(),Decimal("0"))
        if Decimal(closing_total)!=expected_total:raise ValueError(f"Session closing total {closing_total} does not reconcile to posted payments {expected_total}")
        breakdown=(closing_cash,closing_card,closing_bank,closing_other)
        if any(x is not None for x in breakdown):
            if any(x is None for x in breakdown):raise ValueError("All payment-method closing amounts are required when method reconciliation is supplied")
            actual=dict(zip(("cash","card","bank","other"),map(Decimal,breakdown)))
            if actual!=expected:raise ValueError(f"Session payment-method reconciliation mismatch: expected {expected}, got {actual}")
            s.closing_cash=actual["cash"];s.closing_card=actual["card"];s.closing_bank=actual["bank"];s.closing_other=actual["other"]
        s.status="closed";s.closing_total=Decimal(closing_total);s.closed_at=datetime.now(timezone.utc);db.flush();return s

pos_service=POSService()
