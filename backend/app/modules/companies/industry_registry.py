"""Industry behavior registry. Shared ERP modules are enabled by company behavior."""
from dataclasses import dataclass

INDUSTRY_REGISTRY = {
    "restaurant": {"recipes": True, "production": True, "pos": True, "kitchen": True, "waste": True, "tables": True, "delivery": True},
    "cafe": {"recipes": True, "production": True, "pos": True, "kitchen": True, "waste": True, "tables": True, "delivery": True},
    "perfume_manufacturing": {"recipes": True, "production": True, "pos": False, "kitchen": False, "waste": True, "packaging": True, "batch_costing": True, "ecommerce": True},
    # Trading can still use recipes/assemblies for kits, gift sets, packaging and
    # composed products; production is optional behavior, not a different data model.
    "perfume_trading": {"recipes": True, "production": False, "pos": True, "kitchen": False, "waste": True, "packaging": True, "batch_costing": True, "ecommerce": True},
    "retail": {"recipes": True, "production": False, "pos": True, "kitchen": False, "waste": True, "ecommerce": True},
    "manufacturing": {"recipes": True, "production": True, "pos": False, "kitchen": False, "waste": True, "bom": True, "mrp": True, "batch_costing": True},
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
