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


class ReceiptCreate(BaseModel):
    charge_id:int
    payment_date:date
    amount:Decimal=Field(gt=0)
    method:str="cash"
    reference:str|None=None

class ReceiptRead(BaseModel):
    id:int
    charge_id:int
    payment_date:date
    amount:Decimal
    method:str
    reference:str|None=None
    status:str
    journal_entry_id:int|None=None
    model_config={"from_attributes":True}

class RenewalCreate(BaseModel):
    number:str
    start_date:date
    end_date:date
    pricing_type:str|None=None
    fixed_rent:Decimal|None=None
    minimum_guarantee:Decimal|None=None
    revenue_share_percent:Decimal|None=None
    maintenance_amount:Decimal|None=None
    security_deposit:Decimal|None=None
    vat_percent:Decimal|None=None
    wht_percent:Decimal|None=None
    notes:str|None=None


class DepositCreate(BaseModel):
    contract_id:int
    amount:Decimal=Field(gt=0)
    due_date:date|None=None
    notes:str|None=None
class MaintenanceCreate(BaseModel):
    contract_id:int
    unit_id:int
    request_date:date
    category:str="general"
    description:str
    estimated_cost:Decimal=Field(default=Decimal("0"),ge=0)
    actual_cost:Decimal=Field(default=Decimal("0"),ge=0)
    charge_to_tenant:bool=False
    status:str="open"
    completed_date:date|None=None
class InsuranceCreate(BaseModel):
    contract_id:int
    policy_number:str
    insurer:str
    start_date:date
    end_date:date
    coverage_amount:Decimal=Field(default=Decimal("0"),ge=0)
    premium_amount:Decimal=Field(default=Decimal("0"),ge=0)
    status:str="active"
    notes:str|None=None
class DocumentCreate(BaseModel):
    contract_id:int
    document_type:str
    document_number:str|None=None
    file_name:str
    storage_key:str
    issue_date:date|None=None
    expiry_date:date|None=None
    notes:str|None=None
