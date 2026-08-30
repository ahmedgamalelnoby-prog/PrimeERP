from enum import Enum


class TenantStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class BusinessType(str, Enum):
    GENERAL = "general"
    RESTAURANT = "restaurant"
    HOTEL = "hotel"
    RETAIL = "retail"
    REAL_ESTATE = "real_estate"
    SERVICES = "services"
    MANUFACTURING = "manufacturing"


DEFAULT_COUNTRY_CODE = "EG"
DEFAULT_LANGUAGE = "ar"
DEFAULT_LOCALE = "ar-EG"
DEFAULT_TIMEZONE = "Africa/Cairo"
DEFAULT_CURRENCY = "EGP"
DEFAULT_TRIAL_DAYS = 14