from enum import Enum


class AddonType(str, Enum):
    EXTRA_USERS = "extra_users"
    EXTRA_COMPANIES = "extra_companies"
    EXTRA_BRANCHES = "extra_branches"
    EXTRA_WAREHOUSES = "extra_warehouses"
    EXTRA_STORAGE = "extra_storage"
    MODULE = "module"
    INTEGRATION = "integration"
    SUPPORT = "support"
    CUSTOM = "custom"


class AddonPricingType(str, Enum):
    FIXED = "fixed"
    PER_UNIT = "per_unit"
    PER_USER = "per_user"
    USAGE_BASED = "usage_based"


class AddonStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"