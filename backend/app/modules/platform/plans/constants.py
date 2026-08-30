from enum import Enum


class PlanStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class PlanType(str, Enum):
    FREE = "free"
    STANDARD = "standard"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class BillingCycle(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    YEARLY = "yearly"


class PlanCurrency(str, Enum):
    EGP = "EGP"
    USD = "USD"
    EUR = "EUR"
    SAR = "SAR"
    AED = "AED"


DEFAULT_PLAN_CURRENCY = PlanCurrency.EGP

DEFAULT_TRIAL_DAYS = 14
DEFAULT_GRACE_PERIOD_DAYS = 7
DEFAULT_SORT_ORDER = 0

MIN_TRIAL_DAYS = 0
MAX_TRIAL_DAYS = 365

MIN_GRACE_PERIOD_DAYS = 0
MAX_GRACE_PERIOD_DAYS = 90

MIN_SORT_ORDER = 0
MAX_SORT_ORDER = 100_000

PLAN_CODE_MIN_LENGTH = 2
PLAN_CODE_MAX_LENGTH = 50

PLAN_NAME_MIN_LENGTH = 2
PLAN_NAME_MAX_LENGTH = 100

PLAN_DESCRIPTION_MAX_LENGTH = 2_000

PLAN_CODE_PATTERN = r"^[a-z][a-z0-9_-]*$"