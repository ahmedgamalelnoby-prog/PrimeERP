"""Industry behavior registry. Modules stay shared; industry profiles select behavior."""
from dataclasses import dataclass

INDUSTRY_REGISTRY = {
    "restaurant": {
        "recipes": True, "production": True, "pos": True, "kitchen": True,
        "waste": True, "tables": True, "delivery": True,
    },
    "cafe": {
        "recipes": True, "production": True, "pos": True, "kitchen": True,
        "waste": True, "tables": True, "delivery": True,
    },
    "perfume_manufacturing": {
        "recipes": True, "production": True, "pos": False, "kitchen": False,
        "waste": True, "packaging": True, "batch_costing": True, "ecommerce": True,
    },
    "perfume_trading": {
        "recipes": False, "production": False, "pos": True, "kitchen": False,
        "waste": True, "packaging": True, "batch_costing": True, "ecommerce": True,
    },
    "retail": {
        "recipes": False, "production": False, "pos": True, "kitchen": False,
        "waste": True, "ecommerce": True,
    },
    "manufacturing": {
        "recipes": True, "production": True, "pos": False, "kitchen": False,
        "waste": True, "bom": True, "mrp": True, "batch_costing": True,
    },
}

@dataclass(frozen=True)
class IndustryBehavior:
    code: str
    features: dict[str, bool]

    def enabled(self, feature: str) -> bool:
        return bool(self.features.get(feature, False))


def behavior_for(industry_code: str) -> IndustryBehavior:
    code = str(industry_code or "").strip().lower()
    return IndustryBehavior(code=code, features=dict(INDUSTRY_REGISTRY.get(code, {})))
