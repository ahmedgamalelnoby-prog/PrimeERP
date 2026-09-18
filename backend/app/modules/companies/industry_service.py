from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .industry_models import CompanyIndustryProfile
from .industry_registry import IndustryBehavior, behavior_for


def get_industry_behavior(db: Session, company_id: int) -> IndustryBehavior:
    profile = db.scalar(select(CompanyIndustryProfile).where(
        CompanyIndustryProfile.company_id == company_id,
        CompanyIndustryProfile.is_active.is_(True),
    ))
    if profile is None:
        return behavior_for("")
    base = behavior_for(profile.industry_code)
    configured = dict(base.features)
    configured.update({str(k): bool(v) for k, v in (profile.configuration_json or {}).items()})
    return IndustryBehavior(code=base.code, features=configured)


def require_feature(db: Session, company_id: int, feature: str) -> None:
    if not get_industry_behavior(db, company_id).enabled(feature):
        raise ValueError(f"Feature '{feature}' is not enabled for this company's industry profile")
