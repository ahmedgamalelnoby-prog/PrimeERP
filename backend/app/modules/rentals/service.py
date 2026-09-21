from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import RentalProperty,RentalUnit,RentalTenant,RentalContract,RentalCharge

class RentalService:
    def _scope(self, db, model, company_id, tenant_id):
        return select(model).where(model.company_id==company_id, model.tenant_id==tenant_id)

    def create_property(self,db,tenant_id,company_id,payload):
        if db.scalar(self._scope(db,RentalProperty,company_id,tenant_id).where(RentalProperty.code==payload.code)): raise ValueError("Property code already exists")
        obj=RentalProperty(tenant_id=tenant_id,company_id=company_id,**payload.model_dump()); db.add(obj); db.flush(); return obj

    def create_unit(self,db,tenant_id,company_id,payload):
        prop=db.scalar(self._scope(db,RentalProperty,company_id,tenant_id).where(RentalProperty.id==payload.property_id,RentalProperty.is_active.is_(True)))
        if not prop: raise ValueError("Property not found")
        obj=RentalUnit(tenant_id=tenant_id,company_id=company_id,**payload.model_dump()); db.add(obj); db.flush(); return obj

    def create_tenant(self,db,tenant_id,company_id,payload):
        obj=RentalTenant(tenant_id=tenant_id,company_id=company_id,**payload.model_dump()); db.add(obj); db.flush(); return obj

    def create_contract(self,db,tenant_id,company_id,payload):
        unit=db.scalar(self._scope(db,RentalUnit,company_id,tenant_id).where(RentalUnit.id==payload.unit_id,RentalUnit.is_active.is_(True)))
        rt=db.scalar(self._scope(db,RentalTenant,company_id,tenant_id).where(RentalTenant.id==payload.rental_tenant_id,RentalTenant.is_active.is_(True)))
        if not unit or not rt: raise ValueError("Unit or rental tenant not found")
        if payload.end_date<payload.start_date: raise ValueError("Contract end date cannot precede start date")
        if payload.revenue_share_percent>100: raise ValueError("Revenue share cannot exceed 100%")
        obj=RentalContract(tenant_id=tenant_id,company_id=company_id,**payload.model_dump()); db.add(obj); unit.status="reserved"; db.flush(); return obj

    def generate_charge(self,db,tenant_id,company_id,payload):
        c=db.scalar(self._scope(db,RentalContract,company_id,tenant_id).where(RentalContract.id==payload.contract_id))
        if not c: raise ValueError("Contract not found")
        if payload.period_end<payload.period_start: raise ValueError("Invalid charge period")
        fixed=Decimal(c.fixed_rent or 0)
        mg=Decimal(c.minimum_guarantee or 0)
        share=Decimal(payload.revenue_amount or 0)*Decimal(c.revenue_share_percent or 0)/Decimal("100")
        base = max(fixed,mg) if c.pricing_type=="minimum_guarantee" else fixed
        if c.pricing_type=="revenue_share": base=share
        elif c.pricing_type=="fixed_plus_revenue_share": base=fixed+share
        vat=(base+Decimal(c.maintenance_amount or 0))*Decimal(c.vat_percent or 0)/Decimal("100")
        wht=base*Decimal(c.wht_percent or 0)/Decimal("100")
        total=base+Decimal(c.maintenance_amount or 0)+vat-wht
        obj=RentalCharge(tenant_id=tenant_id,company_id=company_id,contract_id=c.id,charge_date=payload.charge_date,period_start=payload.period_start,period_end=payload.period_end,base_amount=base,revenue_amount=payload.revenue_amount,maintenance_amount=c.maintenance_amount,vat_amount=vat,wht_amount=wht,total_amount=total)
        db.add(obj); db.flush(); return obj

    def list_contracts(self,db,tenant_id,company_id):
        return list(db.scalars(self._scope(db,RentalContract,company_id,tenant_id).order_by(RentalContract.start_date.desc())).all())

rental_service=RentalService()
