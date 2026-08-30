from enum import Enum


class FeatureType(str, Enum):
    MODULE = "module"
    FUNCTION = "function"
    LIMIT = "limit"
    INTEGRATION = "integration"


class FeatureValueType(str, Enum):
    BOOLEAN = "boolean"
    INTEGER = "integer"
    DECIMAL = "decimal"
    TEXT = "text"


class FeatureStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"


class FeatureCategory(str, Enum):
    SYSTEM = "system"
    ACCOUNTING = "accounting"
    INVENTORY = "inventory"
    SALES = "sales"
    PURCHASING = "purchasing"
    CRM = "crm"
    HR = "hr"
    PAYROLL = "payroll"
    CONTRACTS = "contracts"
    RESTAURANT = "restaurant"
    HOTELS = "hotels"
    AI = "ai"
    MARKETPLACE = "marketplace"
    INTEGRATIONS = "integrations"