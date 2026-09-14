from pydantic import BaseModel, Field


class CommerceAccountingSettingsCreate(BaseModel):
    company_id: int = Field(gt=0)
    sales_journal_id: int = Field(gt=0)
    purchase_journal_id: int = Field(gt=0)
    cash_journal_id: int = Field(gt=0)
    ar_account_id: int = Field(gt=0)
    ap_account_id: int = Field(gt=0)
    sales_account_id: int = Field(gt=0)
    purchase_account_id: int = Field(gt=0)
    inventory_account_id: int = Field(gt=0)
    grni_account_id: int = Field(gt=0)
    cogs_account_id: int = Field(gt=0)
    output_vat_account_id: int = Field(gt=0)
    input_vat_account_id: int = Field(gt=0)
    wht_account_id: int | None = Field(default=None, gt=0)
    default_payment_account_id: int = Field(gt=0)
    default_branch_id: int = Field(gt=0)
    auto_post: bool = True
