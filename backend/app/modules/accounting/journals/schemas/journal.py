from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

JournalType = Literal["general","sales","purchase","cash","bank","inventory","payroll","adjustment","opening","closing"]

class JournalBase(BaseModel):
    company_id: int = Field(gt=0)
    code: str = Field(min_length=1,max_length=30)
    name_ar: str = Field(min_length=2,max_length=150)
    name_en: str = Field(min_length=2,max_length=150)
    journal_type: JournalType = "general"
    sequence_key: str = Field(default="JOURNAL_ENTRY",min_length=2,max_length=50)
    description: Optional[str] = None
    allow_manual_entries: bool = True
    auto_post: bool = False
    requires_approval: bool = True
    is_active: bool = True

class JournalCreate(JournalBase): pass
class JournalUpdate(BaseModel):
    code: Optional[str]=None
    name_ar: Optional[str]=None
    name_en: Optional[str]=None
    journal_type: Optional[JournalType]=None
    sequence_key: Optional[str]=None
    description: Optional[str]=None
    allow_manual_entries: Optional[bool]=None
    auto_post: Optional[bool]=None
    requires_approval: Optional[bool]=None
    is_active: Optional[bool]=None

class JournalResponse(JournalBase):
    id:int
    tenant_id:int
    created_by:Optional[int]
    updated_by:Optional[int]
    created_at:datetime
    updated_at:datetime
    model_config=ConfigDict(from_attributes=True)

class JournalLineCreate(BaseModel):
    account_combination_id:int=Field(gt=0)
    department_id:Optional[int]=Field(default=None,gt=0)
    cost_center_id:Optional[int]=Field(default=None,gt=0)
    description:Optional[str]=None
    reference:Optional[str]=Field(default=None,max_length=150)
    debit:Decimal=Field(default=Decimal("0"),ge=0)
    credit:Decimal=Field(default=Decimal("0"),ge=0)
    currency_code:str=Field(default="EGP",min_length=3,max_length=3)
    exchange_rate:Decimal=Field(default=Decimal("1"),gt=0)

    @model_validator(mode="after")
    def validate_side(self):
        if (self.debit>0 and self.credit>0) or (self.debit<=0 and self.credit<=0):
            raise ValueError("Each journal line must have debit or credit, not both")
        return self

class JournalEntryCreate(BaseModel):
    company_id:int=Field(gt=0)
    branch_id:int=Field(gt=0)
    journal_id:int=Field(gt=0)
    fiscal_year_id:int=Field(gt=0)
    period_id:int=Field(gt=0)
    entry_date:date
    posting_date:Optional[date]=None
    reference:Optional[str]=Field(default=None,max_length=150)
    description:str=Field(min_length=2)
    currency_code:str=Field(default="EGP",min_length=3,max_length=3)
    exchange_rate:Decimal=Field(default=Decimal("1"),gt=0)
    business_transaction_id:Optional[int]=Field(default=None,gt=0)
    source_module:Optional[str]=Field(default=None,max_length=80)
    source_entity:Optional[str]=Field(default=None,max_length=100)
    source_id:Optional[int]=Field(default=None,gt=0)
    lines:list[JournalLineCreate]=Field(min_length=2)

    @model_validator(mode="after")
    def validate_balanced(self):
        debit=sum((x.debit for x in self.lines),Decimal("0"))
        credit=sum((x.credit for x in self.lines),Decimal("0"))
        if debit != credit:
            raise ValueError("Journal entry must be balanced")
        return self

class JournalEntryUpdate(BaseModel):
    reference:Optional[str]=None
    description:Optional[str]=None
    entry_date:Optional[date]=None

class JournalEntryAction(BaseModel):
    reason:Optional[str]=Field(default=None,max_length=1000)

class JournalEntryLineResponse(JournalLineCreate):
    id:int
    entry_id:int
    line_number:int
    base_debit:Decimal
    base_credit:Decimal
    created_at:datetime
    updated_at:datetime
    model_config=ConfigDict(from_attributes=True)

class JournalEntryResponse(BaseModel):
    id:int
    uuid:str
    tenant_id:int
    company_id:int
    branch_id:int
    journal_id:int
    fiscal_year_id:int
    period_id:int
    business_transaction_id:Optional[int]
    entry_number:str
    entry_date:date
    posting_date:Optional[date]
    reference:Optional[str]
    description:str
    currency_code:str
    exchange_rate:Decimal
    total_debit:Decimal
    total_credit:Decimal
    status:str
    source_module:Optional[str]
    source_entity:Optional[str]
    source_id:Optional[int]
    created_by:Optional[int]
    submitted_by:Optional[int]
    approved_by:Optional[int]
    posted_by:Optional[int]
    cancelled_by:Optional[int]
    created_at:datetime
    submitted_at:Optional[datetime]
    approved_at:Optional[datetime]
    posted_at:Optional[datetime]
    cancelled_at:Optional[datetime]
    updated_at:datetime
    lines:list[JournalEntryLineResponse]=[]
    model_config=ConfigDict(from_attributes=True)
