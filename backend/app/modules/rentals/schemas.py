from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field

class PropertyCreate(BaseModel):
    code:str
    name:str
    branch_id:int|None=None
    address:str|None=None

class UnitCreate(BaseModel):
    property_id:int
    code:str
    name:str
    unit_type:str="commercial"
    area:Decimal|None=None

class TenantCreate(BaseModel):
    code:str
    name:str
    partner_id:int|None=None
    tax_number:str|None=None
    phone:str|None=None
    email:str|None=None

class ContractCreate(BaseModel):
    number:str
    unit_id:int
    rental_tenant_id:int
    branch_id:int|None=None
    start_date:date
    end_date:date
    pricing_type:str="fixed"
    fixed_rent:Decimal=Decimal("0")
    minimum_guarantee:Decimal=Decimal("0")
    revenue_share_percent:Decimal=Decimal("0")
    maintenance_amount:Decimal=Decimal("0")
    security_deposit:Decimal=Decimal("0")
    vat_percent:Decimal=Decimal("0")
    wht_percent:Decimal=Decimal("0")
    notes:str|None=None

class ChargeCreate(BaseModel):
    contract_id:int
    charge_date:date
    period_start:date
    period_end:date
    revenue_amount:Decimal=Decimal("0")

class ChargeRead(BaseModel):
    id:int
    contract_id:int
    base_amount:Decimal
    revenue_amount:Decimal
    maintenance_amount:Decimal
    vat_amount:Decimal
    wht_amount:Decimal
    total_amount:Decimal
    status:str
    model_config={"from_attributes":True}
