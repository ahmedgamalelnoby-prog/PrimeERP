from __future__ import annotations

CORE_TRIAL_MODULES = {
    "dashboard",
    "users",
    "companies",
    "branches",
    "accounting",
    "reports",
}

TRIAL_BUSINESS_MODULES: dict[str, set[str]] = {
    "restaurant": CORE_TRIAL_MODULES | {
        "sales", "inventory", "purchasing", "restaurant", "pos",
    },
    "cafe": CORE_TRIAL_MODULES | {
        "sales", "inventory", "purchasing", "restaurant", "pos",
    },
    "retail": CORE_TRIAL_MODULES | {
        "sales", "inventory", "purchasing", "crm", "pos", "shipping",
    },
    "fashion": CORE_TRIAL_MODULES | {
        "sales", "inventory", "purchasing", "crm", "pos", "shipping",
    },
    "perfume": CORE_TRIAL_MODULES | {
        "sales", "inventory", "purchasing", "crm", "pos", "manufacturing", "shipping",
    },
    "manufacturing": CORE_TRIAL_MODULES | {
        "sales", "inventory", "purchasing", "manufacturing",
    },
    "supermarket": CORE_TRIAL_MODULES | {
        "sales", "inventory", "purchasing", "pos", "crm", "shipping",
    },
    "pharmacy": CORE_TRIAL_MODULES | {
        "sales", "inventory", "purchasing",
    },
    "services": CORE_TRIAL_MODULES | {
        "sales", "crm",
    },
    "other": CORE_TRIAL_MODULES,
}


def trial_modules_for_business(business_type: str | None) -> set[str]:
    return TRIAL_BUSINESS_MODULES.get(
        (business_type or "other").strip().lower(),
        CORE_TRIAL_MODULES,
    )
