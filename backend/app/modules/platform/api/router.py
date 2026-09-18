from fastapi import APIRouter, Depends, HTTPException

from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.platform.module_registry import REGISTRY_VERSION, get_module, list_modules

router = APIRouter(prefix="/platform/modules", tags=["platform-modules"])


@router.get("")
def modules(current_user: User = Depends(get_current_user)) -> dict[str, object]:
    return {"version": REGISTRY_VERSION, "modules": list_modules()}


@router.get("/{module_key}")
def module(module_key: str, current_user: User = Depends(get_current_user)) -> dict[str, object]:
    item = get_module(module_key)
    if item is None:
        raise HTTPException(status_code=404, detail="Module not found")
    return {"version": REGISTRY_VERSION, "module": item}
