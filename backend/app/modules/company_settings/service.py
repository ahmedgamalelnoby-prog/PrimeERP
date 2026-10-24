from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.company_settings.models import CompanySetting
from app.modules.company_settings.registry import BY_KEY


def get_company_setting(db: Session, company_id: int, key: str):
    """Return the company's saved setting or the typed registry default."""
    definition = BY_KEY.get(key)
    if definition is None:
        raise KeyError(f"Unknown company setting: {key}")
    saved = db.scalar(select(CompanySetting.value_json).where(
        CompanySetting.company_id == company_id,
        CompanySetting.setting_key == key,
    ))
    return definition["default"] if saved is None else saved
