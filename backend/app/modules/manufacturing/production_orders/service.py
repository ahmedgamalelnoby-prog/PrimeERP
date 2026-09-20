from __future__ import annotations
from datetime import date
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.completion.domain_models import ManufacturingWorkOrder, ManufacturingConsumption
from app.modules.catalog.models import Recipe, RecipeLine
from app.modules.inventory.stock_moves.schemas import StockMoveCreate
from app.modules.inventory.stock_moves.service import inventory_stock_move_service
from app.modules.inventory.stock_moves.models import InventoryStockMove
from app.modules.companies.models import Company

class ManufacturingProductionService:
    def scope(self,db,company_id,tenant_id):
        c=db.scalar(select(Company).where(Company.id==company_id,Company.tenant_id==tenant_id,Company.is_active.is_(True)))
        if c is None: raise HTTPException(403,"Company is outside the current tenant")
    def create(self,db,**kw):
        self.scope(db,kw["company_id"],kw["tenant_id"])
        if db.scalar(select(ManufacturingWorkOrder.id).where(ManufacturingWorkOrder.company_id==kw["company_id"],ManufacturingWorkOrder.number==kw["number"])):
            raise HTTPException(409,"Work order number already exists")
        if kw.get("recipe_id") and db.scalar(select(Recipe.id).where(Recipe.id==kw["recipe_id"],Recipe.company_id==kw["company_id"],Recipe.product_id==kw["item_id"],Recipe.is_active.is_(True))) is None:
            raise HTTPException(422,"Recipe does not belong to the company/product")
        x=ManufacturingWorkOrder(company_id=kw["company_id"],warehouse_id=kw.get("warehouse_id"),item_id=kw["item_id"],variant_id=kw.get("variant_id"),recipe_id=kw.get("recipe_id"),number=kw["number"],planned_qty=kw["planned_qty"],planned_start=kw.get("planned_start"),planned_end=kw.get("planned_end"))
        # Preserve explicit planned cost inputs when the model exposes them; completion/variance uses these fields when present.
        for _field in ("planned_material_cost","planned_labor_cost","planned_overhead_cost"):
            if _field in kw and hasattr(x,_field): setattr(x,_field,kw[_field])
        db.add(x);db.flush();return x
    def transition(self,db,tenant_id,company_id,work_order_id,status):
        self.scope(db,company_id,tenant_id);x=db.scalar(select(ManufacturingWorkOrder).where(ManufacturingWorkOrder.id==work_order_id,ManufacturingWorkOrder.company_id==company_id).with_for_update())
        if x is None: raise HTTPException(404,"Work order not found")
        allowed={"draft":{"released","cancelled"},"released":{"in_progress","cancelled"},"in_progress":{"completed","cancelled"},"completed":{"closed"},"closed":set(),"cancelled":set()}
        if status!=x.status and status not in allowed.get(x.status,set()): raise HTTPException(409,f"Invalid work-order transition: {x.status} -> {status}")
        x.status=status
        if status=="in_progress": x.actual_start=x.actual_start or date.today()
        if status in {"completed","closed"}: x.actual_end=x.actual_end or date.today()
        db.flush();return x
    def explode(self,db,company_id,recipe_id,qty,seen=None):
        seen=set(seen or ())
        if recipe_id in seen: raise HTTPException(409,"Recursive recipe detected")
        seen.add(recipe_id);r=db.scalar(select(Recipe).where(Recipe.id==recipe_id,Recipe.company_id==company_id,Recipe.is_active.is_(True)))
        if r is None: raise HTTPException(404,"Recipe not found")
        factor=Decimal(qty)/Decimal(r.yield_quantity or 1);out=[]
        for line in db.scalars(select(RecipeLine).where(RecipeLine.recipe_id=r.id).order_by(RecipeLine.line_no)).all():
            q=Decimal(line.quantity)*factor*(1+Decimal(line.waste_percentage or 0)/100)
            nested_q=select(Recipe.id).where(Recipe.company_id==company_id,Recipe.product_id==(line.ingredient_item_id or line.ingredient_product_id),Recipe.is_active.is_(True))
            nested_q=nested_q.where(Recipe.variant_id==line.ingredient_variant_id) if getattr(line,"ingredient_variant_id",None) is not None else nested_q.where(Recipe.variant_id.is_(None))
            nested=db.scalar(nested_q.order_by(Recipe.version.desc()))
            if nested: out.extend(self.explode(db,company_id,nested,q,seen))
            else: out.append({"item_id":line.ingredient_item_id or line.ingredient_product_id,"variant_id":getattr(line,"ingredient_variant_id",None),"quantity":q,"uom_id":line.uom_id})
        return out
    def consume(self,db,tenant_id,user_id,company_id,work_order_id,source_location_id,item_id,quantity,unit_cost=0,variant_id=None):
        self.scope(db,company_id,tenant_id);wo=db.scalar(select(ManufacturingWorkOrder).where(ManufacturingWorkOrder.id==work_order_id,ManufacturingWorkOrder.company_id==company_id).with_for_update())
        if wo is None: raise HTTPException(404,"Work order not found")
        if wo.status not in {"released","in_progress"}: raise HTTPException(409,"Work order must be released or in progress")
        source=f"wo:{wo.id}:consume:{item_id}:{variant_id or 0}:{quantity}"
        existing_move=db.scalar(select(InventoryStockMove).where(
            InventoryStockMove.company_id==company_id,
            InventoryStockMove.source_module=="manufacturing",
            InventoryStockMove.source_entity=="work_order_consumption",
            InventoryStockMove.source_id==source,
            InventoryStockMove.status=="posted",
        ))
        if existing_move is not None:
            return existing_move
        m=inventory_stock_move_service.create_draft(db,StockMoveCreate(company_id=company_id,item_id=item_id,variant_id=variant_id,source_location_id=source_location_id,quantity=quantity,unit_cost=unit_cost,movement_type="issue",reference=wo.number,source_module="manufacturing",source_entity="work_order_consumption",source_id=source))
        inventory_stock_move_service.post(db,tenant_id=tenant_id,company_id=company_id,move_id=m.id,user_id=user_id)
        if db.scalar(select(ManufacturingConsumption.id).where(ManufacturingConsumption.work_order_id==wo.id,ManufacturingConsumption.stock_move_id==m.id)) is None:
            db.add(ManufacturingConsumption(work_order_id=wo.id,item_id=item_id,quantity=quantity,unit_cost=m.unit_cost or 0,stock_move_id=m.id));wo.total_material_cost+=Decimal(m.unit_cost or 0)*Decimal(quantity)
        db.flush();return m
    def complete(self,db,tenant_id,user_id,company_id,work_order_id,destination_location_id,completed_qty,output_unit_cost=None):
        self.scope(db,company_id,tenant_id);wo=db.scalar(select(ManufacturingWorkOrder).where(ManufacturingWorkOrder.id==work_order_id,ManufacturingWorkOrder.company_id==company_id).with_for_update())
        if wo is None: raise HTTPException(404,"Work order not found")
        if wo.status not in {"released","in_progress"}: raise HTTPException(409,"Work order must be released or in progress")
        q=Decimal(completed_qty)
        remaining=Decimal(wo.planned_qty or 0)-Decimal(wo.completed_qty or 0)
        if q<=0 or q>remaining: raise HTTPException(422,"Invalid completed quantity; quantity exceeds remaining work-order quantity")
        cost=Decimal(output_unit_cost) if output_unit_cost is not None else (Decimal(wo.total_material_cost or 0)+Decimal(wo.total_labor_cost or 0)+Decimal(wo.total_overhead_cost or 0))/q
        if cost<=0: raise HTTPException(422,"Production output requires positive valuation")
        output_key=f"wo:{wo.id}:output:{Decimal(wo.completed_qty or 0)}:{q}"
        existing= db.scalar(select(InventoryStockMove).where(InventoryStockMove.company_id==company_id,InventoryStockMove.source_module=="manufacturing",InventoryStockMove.source_entity=="work_order_output",InventoryStockMove.source_id==output_key,InventoryStockMove.status=="posted"))
        if existing is not None: return wo
        m=inventory_stock_move_service.create_draft(db,StockMoveCreate(company_id=company_id,item_id=wo.item_id,variant_id=wo.variant_id,destination_location_id=destination_location_id,quantity=q,unit_cost=cost,movement_type="receipt",reference=wo.number,source_module="manufacturing",source_entity="work_order_output",source_id=output_key))
        inventory_stock_move_service.post(db,tenant_id=tenant_id,company_id=company_id,move_id=m.id,user_id=user_id)
        wo.completed_qty=Decimal(wo.completed_qty or 0)+q
        wo.status="completed" if wo.completed_qty>=Decimal(wo.planned_qty or 0) else "in_progress"
        if wo.status=="completed": wo.actual_end=date.today()
        db.flush();return wo
manufacturing_production_service=ManufacturingProductionService()
