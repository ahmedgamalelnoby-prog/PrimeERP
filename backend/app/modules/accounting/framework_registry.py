from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class AccountingStandard:
    code: str
    title: str
    effective_from: date | None
    category: str


IFRS_STANDARDS = (
    AccountingStandard("IAS_2", "Inventories", None, "measurement"),
    AccountingStandard("IAS_7", "Statement of Cash Flows", None, "presentation"),
    AccountingStandard("IAS_12", "Income Taxes", None, "tax"),
    AccountingStandard("IAS_16", "Property, Plant and Equipment", None, "assets"),
    AccountingStandard("IAS_21", "The Effects of Changes in Foreign Exchange Rates", None, "foreign_exchange"),
    AccountingStandard("IAS_36", "Impairment of Assets", None, "impairment"),
    AccountingStandard("IAS_37", "Provisions, Contingent Liabilities and Contingent Assets", None, "provisions"),
    AccountingStandard("IAS_38", "Intangible Assets", None, "assets"),
    AccountingStandard("IAS_40", "Investment Property", None, "property"),
    AccountingStandard("IFRS_9", "Financial Instruments", None, "financial_instruments"),
    AccountingStandard("IFRS_10", "Consolidated Financial Statements", None, "consolidation"),
    AccountingStandard("IFRS_13", "Fair Value Measurement", None, "valuation"),
    AccountingStandard("IFRS_15", "Revenue from Contracts with Customers", None, "revenue"),
    AccountingStandard("IFRS_16", "Leases", None, "leases"),
    AccountingStandard("IFRS_18", "Presentation and Disclosure in Financial Statements", date(2027, 1, 1), "presentation"),
)


def effective_ifrs_standards(as_of: date) -> tuple[AccountingStandard, ...]:
    return tuple(s for s in IFRS_STANDARDS if s.effective_from is None or s.effective_from <= as_of)


CMA_DOMAINS = (
    "external_financial_reporting",
    "planning_budgeting_forecasting",
    "performance_management",
    "cost_management",
    "internal_controls",
    "technology_analytics",
    "financial_statement_analysis",
    "corporate_finance",
    "business_decision_analysis",
    "enterprise_risk_management",
    "capital_investment_decisions",
    "professional_ethics",
)
