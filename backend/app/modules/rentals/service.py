from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException
from .models import RentalProperty,RentalUnit,RentalTenant,RentalContract,RentalCharge,RentalReceipt
from .accounting_service import rental_accounting_service

class RentalService:
    def _scope(self, model, company_id, tenant_id): return select(model).where(model.company_id==company_id,model.tenant_id==tenant_id)
    def _branch(self, db, branch_id, company_id, tenant_id):
        if branch_id is None: return
        from app.modules.branches.models import Branch
        if db.scalar(select(Branch).where(Branch.id==branch_id,Branch.company_id==company_id,Branch.tenant_id==tenant_id,Branch.is_active.is_(True))) is None: raise HTTPException(400,"Branch is outside the current company/tenant")
    def create_property(self,db,tenant_id,company_id,payload):
        self._branch(db,payload.branch_id,company_id,tenant_id)
        if db.scalar(self._scope(RentalProperty,company_id,tenant_id).where(RentalProperty.code==payload.code)): raise HTTPException(409,"Property code already exists")
        obj=RentalProperty(tenant_id=tenant_id,company_id=company_id,**payload.model_dump());db.add(obj);db.flush();return obj
    def create_unit(self,db,tenant_id,company_id,payload):
        if db.scalar(self._scope(RentalProperty,company_id,tenant_id).where(RentalProperty.id==payload.property_id,RentalProperty.is_active.is_(True))) is None: raise HTTPException(404,"Property not found")
        if db.scalar(self._scope(RentalUnit,company_id,tenant_id).where(RentalUnit.property_id==payload.property_id,RentalUnit.code==payload.code)): raise HTTPException(409,"Unit code already exists for this property")
        obj=RentalUnit(tenant_id=tenant_id,company_id=company_id,**payload.model_dump());db.add(obj);db.flush();return obj
    def create_tenant(self,db,tenant_id,company_id,payload):
        if db.scalar(self._scope(RentalTenant,company_id,tenant_id).where(RentalTenant.code==payload.code)): raise HTTPException(409,"Tenant code already exists")
        if payload.partner_id is not None:
            from app.modules.commerce.models import BusinessPartner
            if db.scalar(select(BusinessPartner).where(BusinessPartner.id==payload.partner_id,BusinessPartner.company_id==company_id,BusinessPartner.is_active.is_(True))) is None: raise HTTPException(404,"Customer/partner not found in this company")
        obj=RentalTenant(tenant_id=tenant_id,company_id=company_id,**payload.model_dump());db.add(obj);db.flush();return obj
    def create_contract(self,db,tenant_id,company_id,payload):
        self._branch(db,payload.branch_id,company_id,tenant_id)
        if db.scalar(self._scope(RentalUnit,company_id,tenant_id).where(RentalUnit.id==payload.unit_id,RentalUnit.is_active.is_(True))) is None: raise HTTPException(404,"Unit not found")
        if db.scalar(self._scope(RentalTenant,company_id,tenant_id).where(RentalTenant.id==payload.rental_tenant_id,RentalTenant.is_active.is_(True))) is None: raise HTTPException(404,"Rental tenant not found")
        if payload.end_date<payload.start_date: raise HTTPException(422,"Contract end date cannot precede start date")
        if payload.revenue_share_percent<0 or payload.revenue_share_percent>100: raise HTTPException(422,"Revenue share must be between 0 and 100")
        overlap=db.scalar(self._scope(RentalContract,company_id,tenant_id).where(RentalContract.unit_id==payload.unit_id,RentalContract.status.in_({"draft","active"}),RentalContract.start_date<=payload.end_date,RentalContract.end_date>=payload.start_date))
        if overlap: raise HTTPException(409,"Unit already has an overlapping rental contract")
        obj=RentalContract(tenant_id=tenant_id,company_id=company_id,**payload.model_dump());db.add(obj);db.flush()
        unit=db.get(RentalUnit,obj.unit_id);unit.status="reserved";return obj
    def activate_contract(self,db,tenant_id,company_id,contract_id):
        obj=db.scalar(self._scope(RentalContract,company_id,tenant_id).where(RentalContract.id==contract_id).with_for_update())
        if obj is None: raise HTTPException(404,"Contract not found")
        if obj.status not in {"draft","renewed"}: raise HTTPException(409,"Contract cannot be activated from its current status")
        obj.status="active";unit=db.get(RentalUnit,obj.unit_id)
        if unit: unit.status="occupied"
        db.flush();return obj
    def terminate_contract(self,db,tenant_id,company_id,contract_id):
        obj=db.scalar(self._scope(RentalContract,company_id,tenant_id).where(RentalContract.id==contract_id).with_for_update())
        if obj is None: raise HTTPException(404,"Contract not found")
        if obj.status not in {"active","draft"}: raise HTTPException(409,"Contract is already closed")
        obj.status="terminated";unit=db.get(RentalUnit,obj.unit_id)
        if unit: unit.status="available"
        db.flush();return obj
    def generate_charge(self,db,tenant_id,company_id,payload,user_id):
        c=db.scalar(self._scope(RentalContract,company_id,tenant_id).where(RentalContract.id==payload.contract_id).with_for_update())
        if not c: raise HTTPException(404,"Contract not found")
        if c.status!="active": raise HTTPException(409,"Only active contracts can be charged")
        if payload.period_end<payload.period_start: raise HTTPException(422,"Invalid charge period")
        if payload.period_start<c.start_date or payload.period_end>c.end_date: raise HTTPException(422,"Charge period must be inside the contract period")
        existing=db.scalar(select(RentalCharge).where(RentalCharge.contract_id==c.id,RentalCharge.period_start==payload.period_start,RentalCharge.period_end==payload.period_end).with_for_update())
        if existing: return existing
        fixed=Decimal(c.fixed_rent or 0);mg=Decimal(c.minimum_guarantee or 0);revenue=Decimal(payload.revenue_amount or 0);share=revenue*Decimal(c.revenue_share_percent or 0)/Decimal("100")
        base=max(fixed,mg) if c.pricing_type=="minimum_guarantee" else fixed
        if c.pricing_type=="revenue_share": base=share
        elif c.pricing_type=="fixed_plus_revenue_share": base=fixed+share
        maintenance=Decimal(c.maintenance_amount or 0);vat=(base+maintenance)*Decimal(c.vat_percent or 0)/Decimal("100");wht=base*Decimal(c.wht_percent or 0)/Decimal("100");total=base+maintenance+vat-wht
        obj=RentalCharge(tenant_id=tenant_id,company_id=company_id,contract_id=c.id,charge_date=payload.charge_date,period_start=payload.period_start,period_end=payload.period_end,base_amount=base,revenue_amount=revenue,maintenance_amount=maintenance,vat_amount=vat,wht_amount=wht,total_amount=total)
        db.add(obj);db.flush();rental_accounting_service.post_charge(db,obj,user_id);return obj
    def list_contracts(self,db,tenant_id,company_id): return list(db.scalars(self._scope(RentalContract,company_id,tenant_id).order_by(RentalContract.start_date.desc())).all())
    def list_charges(self,db,tenant_id,company_id): return list(db.scalars(self._scope(RentalCharge,company_id,tenant_id).order_by(RentalCharge.charge_date.desc()).limit(500)).all())
rental_service=RentalService()


    def collect(self,db,tenant_id,company_id,payload,user_id):
        charge=db.scalar(self._scope(RentalCharge,company_id,tenant_id).where(RentalCharge.id==payload.charge_id).with_for_update())
        if charge is None: raise HTTPException(404,"Charge not found")
        if charge.status not in {"posted","approved"}: raise HTTPException(409,"Charge is not collectible in its current status")
        received=sum((Decimal(r.amount or 0) for r in db.scalars(select(RentalReceipt).where(RentalReceipt.charge_id==charge.id,RentalReceipt.status.in_({"pending","posted"}))).all()),Decimal("0"))
        amount=Decimal(payload.amount)
        if amount<=0: raise HTTPException(422,"Receipt amount must be positive")
        if received+amount>Decimal(charge.total_amount): raise HTTPException(409,"Receipt exceeds outstanding balance")
        receipt=RentalReceipt(tenant_id=tenant_id,company_id=company_id,charge_id=charge.id,payment_date=payload.payment_date,amount=amount,method=payload.method,reference=payload.reference,status="pending")
        db.add(receipt);db.flush()
        from .accounting_service import rental_accounting_service
        rental_accounting_service.post_receipt(db,receipt,user_id)
        return receipt

    def renew_contract(self,db,tenant_id,company_id,contract_id,payload):
        old=db.scalar(self._scope(RentalContract,company_id,tenant_id).where(RentalContract.id==contract_id).with_for_update())
        if old is None: raise HTTPException(404,"Contract not found")
        if old.status not in {"active","terminated"}: raise HTTPException(409,"Only active or terminated contracts can be renewed")
        if payload.start_date<=old.end_date: raise HTTPException(422,"Renewal must start after the previous contract end date")
        if payload.end_date<payload.start_date: raise HTTPException(422,"Invalid renewal dates")
        overlap=db.scalar(self._scope(RentalContract,company_id,tenant_id).where(RentalContract.unit_id==old.unit_id,RentalContract.status.in_({"draft","active","renewed"}),RentalContract.start_date<=payload.end_date,RentalContract.end_date>=payload.start_date))
        if overlap: raise HTTPException(409,"Renewal period overlaps another contract")
        new=RentalContract(tenant_id=tenant_id,company_id=company_id,branch_id=old.branch_id,unit_id=old.unit_id,rental_tenant_id=old.rental_tenant_id,number=payload.number,start_date=payload.start_date,end_date=payload.end_date,status="renewed",pricing_type=payload.pricing_type or old.pricing_type,fixed_rent=payload.fixed_rent if payload.fixed_rent is not None else old.fixed_rent,minimum_guarantee=payload.minimum_guarantee if payload.minimum_guarantee is not None else old.minimum_guarantee,revenue_share_percent=payload.revenue_share_percent if payload.revenue_share_percent is not None else old.revenue_share_percent,maintenance_amount=payload.maintenance_amount if payload.maintenance_amount is not None else old.maintenance_amount,security_deposit=payload.security_deposit if payload.security_deposit is not None else old.security_deposit,vat_percent=payload.vat_percent if payload.vat_percent is not None else old.vat_percent,wht_percent=payload.wht_percent if payload.wht_percent is not None else old.wht_percent,notes=payload.notes)
        db.add(new);old.status="terminated";db.flush();return new
