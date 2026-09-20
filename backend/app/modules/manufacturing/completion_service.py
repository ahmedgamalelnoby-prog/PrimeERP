from datetime import date
from decimal import Decimal
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.modules.manufacturing.completion_models import *
from app.modules.completion.domain_models import ManufacturingWorkOrder,ManufacturingConsumption
from app.modules.inventory.stock_moves.models import InventoryStockMove

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
    def byproduct(self,db,company_id,work_order_id,**kw):
        self._wo(db,company_id,work_order_id);x=ManufacturingByProduct(company_id=company_id,work_order_id=work_order_id,**kw);db.add(x);db.flush();return x
    def subcontract(self,db,company_id,work_order_id,**kw):
        self._wo(db,company_id,work_order_id);x=ManufacturingSubcontract(company_id=company_id,work_order_id=work_order_id,**kw);db.add(x);db.flush();return x
    def variance(self,db,company_id,work_order_id):
        wo=self._wo(db,company_id,work_order_id)
        planned_m=Decimal(wo.total_material_cost or 0); actual_m=sum((Decimal(x.unit_cost or 0)*Decimal(x.quantity or 0) for x in db.scalars(select(ManufacturingConsumption).where(ManufacturingConsumption.work_order_id==wo.id)),),Decimal("0"))
        planned_l=Decimal(0); actual_l=Decimal(db.scalar(select(func.coalesce(func.sum(ManufacturingLaborActual.amount),0)).where(ManufacturingLaborActual.work_order_id==wo.id)) or 0)
        planned_o=Decimal(wo.total_overhead_cost or 0); actual_o=Decimal(db.scalar(select(func.coalesce(func.sum(ManufacturingOverheadActual.amount),0)).where(ManufacturingOverheadActual.work_order_id==wo.id)) or 0)
        scrap=Decimal(db.scalar(select(func.coalesce(func.sum(ManufacturingScrap.quantity*ManufacturingScrap.unit_cost),0)).where(ManufacturingScrap.work_order_id==wo.id)) or 0)
        byp=Decimal(db.scalar(select(func.coalesce(func.sum(ManufacturingByProduct.quantity*ManufacturingByProduct.unit_cost),0)).where(ManufacturingByProduct.work_order_id==wo.id)) or 0)
        total=(actual_m-planned_m)+(actual_l-planned_l)+(actual_o-planned_o)+scrap-byp
        x=db.scalar(select(ManufacturingVariance).where(ManufacturingVariance.work_order_id==wo.id,ManufacturingVariance.status=="calculated").order_by(ManufacturingVariance.id.desc()))
        if x is None: x=ManufacturingVariance(company_id=company_id,work_order_id=wo.id)
        x.planned_material=planned_m;x.actual_material=actual_m;x.planned_labor=planned_l;x.actual_labor=actual_l;x.planned_overhead=planned_o;x.actual_overhead=actual_o;x.scrap_cost=scrap;x.byproduct_credit=byp;x.total_variance=total;x.status="calculated";db.add(x);db.flush();return x
manufacturing_completion_service=ManufacturingCompletionService()
