from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.audit.service import record_audit_event
from app.modules.companies.models import Company
from app.modules.company_settings.models import CompanySetting
from app.modules.company_settings.registry import BY_KEY, CATALOG, validate_value
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User

router = APIRouter(prefix="/company-settings", tags=["Company Policy Settings"])


class SettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    settings: dict[str, object] = Field(min_length=1, max_length=100)


def _company(db: Session, company_id: int, user: User) -> Company:
    tenant_id = get_effective_tenant_id(user)
    company = db.scalar(select(Company).where(
        Company.id == company_id, Company.tenant_id == tenant_id, Company.is_active.is_(True)
    ))
    if company is None:
        raise HTTPException(status_code=404, detail="Active company not found in current tenant")
    return company


@router.get("", dependencies=[Depends(require_permission("company.access"))])
def get_company_settings(
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    company = _company(db, company_id, user)
    stored = {
        row.setting_key: row.value_json
        for row in db.scalars(select(CompanySetting).where(
            CompanySetting.company_id == company.id,
            CompanySetting.tenant_id == company.tenant_id,
        )).all()
    }
    return {
        "company_id": company.id,
        "company_name": company.name,
        "categories": list(dict.fromkeys(item["category"] for item in CATALOG)),
        "settings": [
            {**item, "value": stored.get(item["key"], item["default"])}
            for item in CATALOG
        ],
    }


@router.put("", dependencies=[Depends(require_permission("company.write"))])
def update_company_settings(
    payload: SettingsUpdate,
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    company = _company(db, company_id, user)
    unknown = sorted(set(payload.settings) - set(BY_KEY))
    if unknown:
        raise HTTPException(status_code=422, detail={"message": "Unknown setting keys", "keys": unknown})
    validated = {}
    try:
        for key, value in payload.settings.items():
            validated[key] = validate_value(key, value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    changed = []
    for key, value in validated.items():
        row = db.scalar(select(CompanySetting).where(
            CompanySetting.company_id == company.id,
            CompanySetting.tenant_id == company.tenant_id,
            CompanySetting.setting_key == key,
        ).with_for_update())
        old_value = row.value_json if row else BY_KEY[key]["default"]
        if old_value == value:
            continue
        if row is None:
            row = CompanySetting(
                tenant_id=company.tenant_id, company_id=company.id,
                setting_key=key, value_json=value, updated_by=user.id,
            )
            db.add(row)
        else:
            row.value_json = value
            row.updated_by = user.id
        changed.append({"key": key, "old": old_value, "new": value})

    try:
        if changed:
            record_audit_event(
                db, action="company.policy_settings_updated",
                entity_type="company", entity_id=company.id,
                tenant_id=company.tenant_id, company_id=company.id, user_id=user.id,
                metadata={"changed_keys": [item["key"] for item in changed]},
            )
            db.commit()
    except Exception:
        db.rollback()
        raise
    return {"company_id": company.id, "updated_keys": [item["key"] for item in changed], "updated_count": len(changed)}
