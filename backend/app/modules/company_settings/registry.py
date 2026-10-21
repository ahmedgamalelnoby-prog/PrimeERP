"""Typed, centrally-defined company policy catalog. Secrets belong in the integrations credential vault, never here."""
import math
import re
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# status='catalog' means persisted and visible, but the owning workflow still needs to consume it before it changes transactions.
# status='runtime' is reserved for options whose behavior is enforced by a workflow.
_RAW = [
    # Company-wide defaults
    ("general.default_language","general","General","enum","ar","Interface language",["ar","en"],"runtime"),
    ("general.date_format","general","General","enum","DD/MM/YYYY","Date display format",["DD/MM/YYYY","MM/DD/YYYY","YYYY-MM-DD"],"catalog"),
    ("general.timezone","general","General","string","Africa/Cairo","Company timezone",None,"runtime"),
    ("general.base_currency","general","General","string","EGP","Functional currency code",None,"runtime"),
    ("general.allow_multi_currency","general","General","bool",True,"Allow foreign-currency transactions",None,"runtime"),
    ("general.require_cost_center","general","General","bool",False,"Require cost center where supported",None,"runtime"),
    ("general.require_project","general","General","bool",False,"Require project dimension where supported",None,"catalog"),
    ("general.branch_required","general","General","bool",False,"Require branch on company transactions",None,"runtime"),
    ("general.intercompany_enabled","general","General","bool",False,"Enable intercompany workflows",None,"runtime"),
    # Accounting and tax
    ("accounting.period_lock_enabled","accounting","Accounting","bool",True,"Prevent posting into closed periods",None,"runtime"),
    ("accounting.allow_backdated_entries","accounting","Accounting","bool",False,"Allow backdated entries subject to period controls",None,"runtime"),
    ("accounting.require_journal_approval","accounting","Accounting","bool",True,"Require approval before journal posting",None,"runtime"),
    ("accounting.auto_post_sales_invoice","accounting","Accounting","bool",False,"Automatically post eligible sales invoices",None,"runtime"),
    ("accounting.auto_post_purchase_invoice","accounting","Accounting","bool",False,"Automatically post eligible purchase invoices",None,"runtime"),
    ("accounting.rounding_method","accounting","Accounting","enum","currency","Document rounding policy",["currency","half_up","bankers","none"],"runtime"),
    ("accounting.fiscal_year_start_month","accounting","Accounting","int",1,"First month of fiscal year",None,"runtime"),
    ("accounting.default_receivable_account","accounting","Accounting","string","","Default receivable account code",None,"runtime"),
    ("accounting.default_payable_account","accounting","Accounting","string","","Default payable account code",None,"runtime"),
    ("accounting.default_sales_account","accounting","Accounting","string","","Default sales account code",None,"runtime"),
    ("accounting.default_purchase_account","accounting","Accounting","string","","Default purchase account code",None,"runtime"),
    ("accounting.default_cash_account","accounting","Accounting","string","","Default cash account code",None,"runtime"),
    ("tax.default_tax_inclusive_pricing","taxes","Taxes","bool",False,"Sales prices include tax by default",None,"runtime"),
    ("tax.require_tax_code_on_invoice","taxes","Taxes","bool",True,"Require tax code on taxable invoices",None,"runtime"),
    ("tax.einvoice_required_for_sales","egyptian-einvoice","Taxes","bool",False,"Require a valid Egyptian e-invoice before sales invoice confirmation",None,"runtime"),
    # Sales / customer credit
    ("sales.require_quote_approval","sales","Sales","bool",False,"Require quotation approval above configured limits",None,"catalog"),
    ("sales.require_order_approval","sales","Sales","bool",True,"Require sales order approval",None,"catalog"),
    ("sales.invoice_requires_delivery","sales","Sales","bool",False,"Require delivery before invoicing stock items",None,"catalog"),
    ("sales.allow_overbilling","sales","Sales","bool",False,"Allow billing above ordered quantity",None,"catalog"),
    ("sales.credit_limit_enforced","sales","Sales","bool",True,"Block orders beyond customer credit limit",None,"runtime"),
    ("sales.allow_negative_customer_balance","sales","Sales","bool",False,"Allow defined customer balance exceptions",None,"catalog"),
    ("sales.default_payment_terms_days","sales","Sales","int",30,"Default customer payment term",None,"runtime"),
    ("sales.document_numbering","sales","Sales","enum","per_company_year","Sales document numbering policy",["per_company_year","per_company","global"],"catalog"),
    # Procurement / suppliers
    ("purchasing.require_purchase_order","purchasing","Purchasing","bool",True,"Require PO before supplier invoice",None,"catalog"),
    ("purchasing.require_purchase_approval","purchasing","Purchasing","bool",True,"Require purchase order approval",None,"catalog"),
    ("purchasing.require_goods_receipt","purchasing","Purchasing","bool",True,"Require receipt before supplier invoice",None,"runtime"),
    ("purchasing.allow_invoice_price_variance","purchasing","Purchasing","bool",False,"Allow invoice price variance beyond tolerance",None,"runtime"),
    ("purchasing.price_variance_tolerance_pct","purchasing","Purchasing","number",0,"Allowed price variance percentage",None,"runtime"),
    ("purchasing.default_payment_terms_days","purchasing","Purchasing","int",30,"Default supplier payment term",None,"runtime"),
    # Inventory
    ("inventory.allow_negative_stock","inventory","Inventory","bool",False,"Allow stock to fall below zero where the valuation method supports it",None,"runtime"),
    ("inventory.valuation_method","inventory","Inventory","enum","fifo","Inventory costing method for supported flows",["fifo","moving_average","standard_cost"],"catalog"),
    ("inventory.require_warehouse","inventory","Inventory","bool",True,"Require warehouse on stock transactions",None,"runtime"),
    ("inventory.require_bin_location","inventory","Inventory","bool",False,"Require a storage/bin location",None,"runtime"),
    ("inventory.auto_reserve_sales_orders","inventory","Inventory","bool",False,"Reserve stock on sales order confirmation",None,"catalog"),
    ("inventory.allow_below_cost_sale","inventory","Inventory","bool",False,"Allow sale below cost subject to permission",None,"catalog"),
    ("inventory.expiry_tracking_required","inventory","Inventory","bool",False,"Require expiry dates for perishable/batch items",None,"catalog"),
    ("inventory.serial_tracking_default","inventory","Inventory","bool",False,"Default serial tracking for eligible items",None,"catalog"),
    ("inventory.batch_tracking_default","inventory","Inventory","bool",False,"Default batch/lot tracking for eligible items",None,"catalog"),
    # HR
    ("hr.attendance_source","hr","Human Resources","enum","manual","Attendance source",["manual","biometric","mobile","integration"],"catalog"),
    ("hr.require_attendance_approval","hr","Human Resources","bool",True,"Require attendance corrections approval",None,"catalog"),
    ("hr.overtime_requires_approval","hr","Human Resources","bool",True,"Require overtime approval",None,"catalog"),
    ("hr.leave_requires_approval","hr","Human Resources","bool",True,"Require leave approval",None,"catalog"),
    ("hr.payroll_requires_approval","hr","Human Resources","bool",True,"Require payroll approval before posting",None,"catalog"),
    ("hr.allow_negative_leave_balance","hr","Human Resources","bool",False,"Allow leave balance below zero",None,"catalog"),
    ("hr.default_work_hours_per_day","hr","Human Resources","number",8,"Default scheduled hours per workday",None,"catalog"),
    ("hr.biometric_sync_interval_minutes","hr","Human Resources","int",15,"Target sync interval for biometric integrations",None,"catalog"),
    # Approvals / operations / POS
    ("workflow.approval_mode","approvals","Approvals","enum","sequential","Approval chain mode",["sequential","parallel","any_one"],"catalog"),
    ("workflow.allow_self_approval","approvals","Approvals","bool",False,"Allow requester to approve their own request",None,"runtime"),
    ("workflow.escalation_after_hours","approvals","Approvals","int",24,"Escalate pending approvals after hours",None,"catalog"),
    ("pos.allow_open_cash_drawer","pos","Point of Sale","bool",False,"Allow cash drawer opening without a transaction",None,"catalog"),
    ("pos.require_shift_close","pos","Point of Sale","bool",True,"Require cashier shift closing and reconciliation",None,"catalog"),
    ("pos.allow_discount_without_approval","pos","Point of Sale","bool",False,"Allow cashier discounts without approval",None,"runtime"),
    ("pos.max_discount_pct_without_approval","pos","Point of Sale","number",0,"Maximum discount without approval",None,"runtime"),
    # Manufacturing / service / integrations
    ("manufacturing.require_work_order","manufacturing","Manufacturing","bool",True,"Require work order for production",None,"catalog"),
    ("manufacturing.allow_overproduction","manufacturing","Manufacturing","bool",False,"Allow production above planned quantity",None,"catalog"),
    ("crm.duplicate_customer_check","crm","CRM","bool",True,"Warn/block likely duplicate customers",None,"runtime"),
    ("integrations.auto_sync_enabled","integrations","Integrations","bool",False,"Enable automatic sync for configured integrations",None,"catalog"),
    ("integrations.retry_limit","integrations","Integrations","int",5,"Retry count for transient integration failures",None,"runtime"),
    ("integrations.webhook_signature_required","integrations","Integrations","bool",True,"Require signatures for supported inbound webhooks",None,"runtime"),
    
]
CATALOG: list[dict[str, Any]] = [
    {"key":key,"module":module,"category":category,"type":kind,"default":default,"label":label,
     "choices":choices,"status":status}
    for key,module,category,kind,default,label,choices,status in _RAW
]
BY_KEY = {item["key"]: item for item in CATALOG}


def validate_value(key: str, value: Any) -> Any:
    item = BY_KEY.get(key)
    if item is None:
        raise ValueError(f"Unknown company setting: {key}")
    kind = item["type"]
    if kind == "bool" and not isinstance(value, bool):
        raise ValueError(f"{key} must be true or false")
    if kind == "int" and (isinstance(value, bool) or not isinstance(value, int)):
        raise ValueError(f"{key} must be an integer")
    if kind == "number" and (
        isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value))
    ):
        raise ValueError(f"{key} must be a finite number")
    if kind == "string" and (not isinstance(value, str) or len(value) > 200):
        raise ValueError(f"{key} must be text up to 200 characters")
    if kind == "enum" and (not isinstance(value, str) or value not in item["choices"]):
        raise ValueError(f"{key} has an unsupported option")

    if key == "general.timezone":
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, TypeError):
            raise ValueError(f"{key} must be a valid IANA timezone") from None
    if key == "general.base_currency" and not re.fullmatch(r"[A-Z]{3}", value):
        raise ValueError(f"{key} must be a 3-letter uppercase currency code")
    if key.endswith("fiscal_year_start_month") and not 1 <= value <= 12:
        raise ValueError(f"{key} must be between 1 and 12")
    if key == "hr.default_work_hours_per_day" and not 0 < float(value) <= 24:
        raise ValueError(f"{key} must be greater than 0 and at most 24")
    if kind == "int" and ("days" in key or "hours" in key or "minutes" in key or "limit" in key) and not 0 <= value <= 10000:
        raise ValueError(f"{key} must be between 0 and 10000")
    if kind == "number" and not 0 <= float(value) <= 100:
        raise ValueError(f"{key} must be between 0 and 100")
    return value
