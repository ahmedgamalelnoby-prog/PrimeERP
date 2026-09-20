from datetime import date
from decimal import Decimal
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.modules.manufacturing.completion_models import *
from app.modules.completion.domain_models import ManufacturingWorkOrder,ManufacturingConsumption
from app.modules.inventory.stock_moves.models import InventoryStockMove
from app.modules.inventory.stock_moves.schemas import StockMoveCreate
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.catalog.models import Recipe, RecipeLine
from app.modules.inventory.stock_moves.service import inventory_stock_move_service
from app.modules.accounting.journals.services.journal_service import journal_service

class ManufacturingCompletionService:
    def _wo(self,db,company_id,work_order_id):
        x=db.scalar(select(ManufacturingWorkOrder).where(ManufacturingWorkOrder.id==work_order_id,ManufacturingWorkOrder.company_id==company_id).with_for_update())
        if x is None: raise HTTPException(404,"Work order not found")
        return x
    def labor(self,db,company_id,work_order_id,**kw):
        self._wo(db,company_id,work_order_id)
        amount=Decimal(str(kw["minutes"]))*Decimal(str(kw["hourly_rate"]))/Decimal("60")
        x=ManufacturingLaborActual(company_id=company_id,work_order_id=work_order_id,amount=amount,**kw);db.add(x);db.flush();return x
    def overhead(self,db,company_id,work_order_id,**kw):
        self._wo(db,company_id,work_order_id);x=ManufacturingOverheadActual(company_id=company_id,work_order_id=work_order_id,**kw);db.add(x);db.flush();return x
    def scrap(self,db,company_id,work_order_id,**kw):
        self._wo(db,company_id,work_order_id);x=ManufacturingScrap(company_id=company_id,work_order_id=work_order_id,**kw);db.add(x);db.flush();return x
    def stock_backed_scrap(self,db,tenant_id,company_id,work_order_id,p,user_id):
        self._wo(db,company_id,work_order_id)
        x=ManufacturingScrap(company_id=company_id,work_order_id=work_order_id,item_id=p.item_id,variant_id=p.variant_id,quantity=p.quantity,unit_cost=p.unit_cost,reason=p.notes or "Production scrap")
        db.add(x);db.flush()
        p.source_id=str(x.id);p.source_module="manufacturing";p.source_entity="production_scrap"
        move=inventory_stock_move_service.create_draft(db,p)
        move=inventory_stock_move_service.post(db,tenant_id=tenant_id,company_id=company_id,move_id=move.id,user_id=user_id)
        x.stock_move_id=move.id;db.flush();return x
    def byproduct(self,db,company_id,work_order_id,**kw):
        self._wo(db,company_id,work_order_id);x=ManufacturingByProduct(company_id=company_id,work_order_id=work_order_id,**kw);db.add(x);db.flush();return x
    def stock_backed_byproduct(self,db,tenant_id,company_id,work_order_id,p,user_id):
        self._wo(db,company_id,work_order_id)
        x=ManufacturingByProduct(company_id=company_id,work_order_id=work_order_id,item_id=p.item_id,variant_id=p.variant_id,quantity=p.quantity,unit_cost=p.unit_cost)
        db.add(x);db.flush()
        p.source_id=str(x.id);p.source_module="manufacturing";p.source_entity="production_byproduct"
        move=inventory_stock_move_service.create_draft(db,p)
        move=inventory_stock_move_service.post(db,tenant_id=tenant_id,company_id=company_id,move_id=move.id,user_id=user_id)
        x.stock_move_id=move.id;db.flush();return x
    def execute_production(self,db,tenant_id,company_id,work_order_id,user_id,quantity,source_location_id=None,destination_location_id=None):
        wo=self._wo(db,company_id,work_order_id)
        qty=Decimal(str(quantity))
        if qty <= 0: raise HTTPException(400,"Production quantity must be positive")
        starting_completed=Decimal(wo.completed_qty or 0)
        remaining=Decimal(wo.planned_qty or 0)-starting_completed
        if qty > remaining: raise HTTPException(409,"Production quantity exceeds remaining work-order quantity")
        if wo.recipe_id is None: raise HTTPException(409,"Work order has no recipe")
        recipe=db.scalar(select(Recipe).where(Recipe.id==wo.recipe_id,Recipe.company_id==company_id,Recipe.is_active.is_(True)))
        if recipe is None: raise HTTPException(404,"Recipe not found")
        if source_location_id is None:
            source_location_id=db.scalar(select(InventoryLocation.id).where(InventoryLocation.company_id==company_id,InventoryLocation.warehouse_id==wo.warehouse_id,InventoryLocation.is_active.is_(True),InventoryLocation.location_type=="storage").order_by(InventoryLocation.id).limit(1))
        if destination_location_id is None: destination_location_id=db.scalar(select(InventoryLocation.id).where(InventoryLocation.company_id==company_id,InventoryLocation.warehouse_id==wo.warehouse_id,InventoryLocation.is_active.is_(True),InventoryLocation.location_type.in_(["receiving","storage"])).order_by(InventoryLocation.location_type.desc(),InventoryLocation.id).limit(1))
        if source_location_id is None or destination_location_id is None: raise HTTPException(409,"Production requires active source and destination warehouse locations")
        if source_location_id == destination_location_id: raise HTTPException(409,"Production source and destination locations must differ")
        scale=qty/Decimal(recipe.yield_quantity or 1)
        material_total=Decimal("0")
        for line in db.scalars(select(RecipeLine).where(RecipeLine.recipe_id==recipe.id).order_by(RecipeLine.line_no)).all():
            item_id=line.ingredient_item_id or line.ingredient_product_id
            required=Decimal(line.quantity or 0)*scale*(Decimal("1")+Decimal(line.waste_percentage or 0)/Decimal("100"))
            payload=StockMoveCreate(company_id=company_id,item_id=item_id,quantity=required,unit_cost=Decimal("0"),movement_type="issue",source_location_id=source_location_id,transaction_date=date.today(),source_module="manufacturing",source_entity="production_material",source_id=f"{work_order_id}:{line.id}:{starting_completed}:{qty}",notes=f"Material consumption for work order {work_order_id}")
            move=inventory_stock_move_service.create_draft(db,payload)
            move=inventory_stock_move_service.post(db,tenant_id=tenant_id,company_id=company_id,move_id=move.id,user_id=user_id)
            existing=db.scalar(select(ManufacturingConsumption).where(ManufacturingConsumption.work_order_id==wo.id,ManufacturingConsumption.stock_move_id==move.id))
            if existing is None:
                existing=ManufacturingConsumption(work_order_id=wo.id,item_id=item_id,quantity=required,unit_cost=move.unit_cost or 0,stock_move_id=move.id);db.add(existing)
            material_total += Decimal(move.unit_cost or 0)*required
        actual_l=Decimal(db.scalar(select(func.coalesce(func.sum(ManufacturingLaborActual.amount),0)).where(ManufacturingLaborActual.work_order_id==wo.id)) or 0)
        actual_o=Decimal(db.scalar(select(func.coalesce(func.sum(ManufacturingOverheadActual.amount),0)).where(ManufacturingOverheadActual.work_order_id==wo.id)) or 0)
        subcontract=Decimal(db.scalar(select(func.coalesce(func.sum(ManufacturingSubcontract.actual_quantity*ManufacturingSubcontract.unit_cost),0)).where(ManufacturingSubcontract.work_order_id==wo.id,ManufacturingSubcontract.status!="cancelled")) or 0)
        cumulative_cost=material_total+actual_l+actual_o+subcontract
        prior_output_value=Decimal(db.scalar(select(func.coalesce(func.sum(InventoryStockMove.quantity*InventoryStockMove.unit_cost),0)).where(InventoryStockMove.company_id==company_id,InventoryStockMove.source_module=="manufacturing",InventoryStockMove.source_entity=="production_output",InventoryStockMove.source_id.like(f"{work_order_id}:%"),InventoryStockMove.status=="posted")) or 0)
        incremental_cost=cumulative_cost-prior_output_value
        if incremental_cost < 0: incremental_cost=Decimal("0")
        unit_cost=incremental_cost/qty if qty else Decimal("0")
        payload=StockMoveCreate(company_id=company_id,item_id=wo.item_id,variant_id=wo.variant_id,quantity=qty,unit_cost=unit_cost,movement_type="receipt",destination_location_id=destination_location_id,transaction_date=date.today(),source_module="manufacturing",source_entity="production_output",source_id=f"{work_order_id}:{qty}:{Decimal(wo.completed_qty or 0)}",notes=f"Finished goods receipt for work order {work_order_id}")
        output=inventory_stock_move_service.create_draft(db,payload)
        output=inventory_stock_move_service.post(db,tenant_id=tenant_id,company_id=company_id,move_id=output.id,user_id=user_id)
        wo.completed_qty=Decimal(wo.completed_qty or 0)+qty
        wo.status="completed" if wo.completed_qty >= Decimal(wo.planned_qty or 0) else "in_progress"
        wo.total_material_cost=Decimal(wo.total_material_cost or 0)+material_total
        if wo.actual_start is None: wo.actual_start=date.today()
        if wo.completed_qty >= Decimal(wo.planned_qty or 0): wo.actual_end=date.today()
        db.flush()
        return {"work_order_id":wo.id,"produced_quantity":qty,"completed_quantity":wo.completed_qty,"remaining_quantity":Decimal(wo.planned_qty or 0)-Decimal(wo.completed_qty or 0),"status":wo.status,"material_cost":material_total,"finished_goods_unit_cost":unit_cost,"output_stock_move_id":output.id}

    def subcontract(self,db,company_id,work_order_id,**kw):
        self._wo(db,company_id,work_order_id);x=ManufacturingSubcontract(company_id=company_id,work_order_id=work_order_id,**kw);db.add(x);db.flush();return x
    def post_variance(self,db,company_id,work_order_id,*,tenant_id,user_id,journal_id,fiscal_year_id,period_id,branch_id,entry_number,entry_date,debit_account_id,credit_account_id):
        x=self.variance(db,company_id,work_order_id)
        amount=abs(Decimal(x.total_variance or 0))
        if amount == 0: raise HTTPException(409,"Manufacturing variance is zero; nothing to post")
        debit,credit=(debit_account_id,credit_account_id) if Decimal(x.total_variance or 0) >= 0 else (credit_account_id,debit_account_id)
        entry=journal_service.create_draft(db,tenant_id=tenant_id,company_id=company_id,branch_id=branch_id,journal_id=journal_id,fiscal_year_id=fiscal_year_id,period_id=period_id,entry_number=entry_number,entry_date=entry_date,description=f"Manufacturing variance for work order {work_order_id}",lines=[{"account_combination_id":debit,"debit":amount,"credit":0},{"account_combination_id":credit,"debit":0,"credit":amount}],user_id=user_id,source_module="manufacturing",source_entity="production_variance",source_id=work_order_id,commit=False)
        journal_service.submit(db,tenant_id=tenant_id,entry_id=entry.id,user_id=user_id,commit=False)
        journal_service.post(db,tenant_id=tenant_id,entry_id=entry.id,user_id=user_id,commit=False)
        x.journal_entry_id=entry.id;x.status="posted";db.flush();return x
    def variance(self,db,company_id,work_order_id):
        wo=self._wo(db,company_id,work_order_id)
        if getattr(wo,"status",None) in {"cancelled","closed"}:
            x=db.scalar(select(ManufacturingVariance).where(ManufacturingVariance.work_order_id==wo.id,ManufacturingVariance.status.in_(["calculated","posted"])).order_by(ManufacturingVariance.id.desc()))
            if x is None:
                raise HTTPException(409,"Closed or cancelled work orders require a calculated variance before finalization")
            return x
        planned_m=Decimal(wo.total_material_cost or 0); actual_m=sum((Decimal(x.unit_cost or 0)*Decimal(x.quantity or 0) for x in db.scalars(select(ManufacturingConsumption).where(ManufacturingConsumption.work_order_id==wo.id))),Decimal("0"))
        planned_l=Decimal(0); actual_l=Decimal(db.scalar(select(func.coalesce(func.sum(ManufacturingLaborActual.amount),0)).where(ManufacturingLaborActual.work_order_id==wo.id)) or 0)
        planned_o=Decimal(wo.total_overhead_cost or 0); actual_o=Decimal(db.scalar(select(func.coalesce(func.sum(ManufacturingOverheadActual.amount),0)).where(ManufacturingOverheadActual.work_order_id==wo.id)) or 0)
        scrap=Decimal(db.scalar(select(func.coalesce(func.sum(ManufacturingScrap.quantity*ManufacturingScrap.unit_cost),0)).where(ManufacturingScrap.work_order_id==wo.id)) or 0)
        byp=Decimal(db.scalar(select(func.coalesce(func.sum(ManufacturingByProduct.quantity*ManufacturingByProduct.unit_cost),0)).where(ManufacturingByProduct.work_order_id==wo.id)) or 0)
        subcontract=Decimal(db.scalar(select(func.coalesce(func.sum(ManufacturingSubcontract.actual_quantity*ManufacturingSubcontract.unit_cost),0)).where(ManufacturingSubcontract.work_order_id==wo.id,ManufacturingSubcontract.status!="cancelled")) or 0)
        total=(actual_m-planned_m)+(actual_l-planned_l)+(actual_o-planned_o)+subcontract+scrap-byp
        x=db.scalar(select(ManufacturingVariance).where(ManufacturingVariance.work_order_id==wo.id,ManufacturingVariance.status=="calculated").order_by(ManufacturingVariance.id.desc()))
        if x is None: x=ManufacturingVariance(company_id=company_id,work_order_id=wo.id)
        x.planned_material=planned_m;x.actual_material=actual_m;x.planned_labor=planned_l;x.actual_labor=actual_l;x.planned_overhead=planned_o;x.actual_overhead=actual_o;x.scrap_cost=scrap;x.byproduct_credit=byp;x.subcontract_cost=subcontract;x.total_variance=total;x.status="calculated";db.add(x);db.flush();return x
manufacturing_completion_service=ManufacturingCompletionService()
