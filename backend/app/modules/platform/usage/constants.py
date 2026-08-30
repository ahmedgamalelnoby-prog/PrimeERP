from enum import Enum


class UsageMetric(str, Enum):
    USERS = "users"
    COMPANIES = "companies"
    BRANCHES = "branches"
    WAREHOUSES = "warehouses"
    STORAGE_GB = "storage_gb"
    API_REQUESTS = "api_requests"
    DOCUMENTS = "documents"
    INVOICES = "invoices"
    TRANSACTIONS = "transactions"


class UsagePeriod(str, Enum):
    DAILY = "daily"
    MONTHLY = "monthly"
    BILLING_CYCLE = "billing_cycle"
    LIFETIME = "lifetime"