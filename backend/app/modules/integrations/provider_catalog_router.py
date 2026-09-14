from fastapi import APIRouter, Depends, Query

from app.core.permissions import require_permission
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.saas.entitlements import require_module
from .provider_catalog import list_providers

router = APIRouter(
    prefix="/integrations/providers",
    tags=["Integration Providers"],
    dependencies=[Depends(require_permission("integrations.access")), Depends(require_module("integrations"))],
)


@router.get("")
def providers(category: str | None = Query(default=None), _: User = Depends(get_current_user)):
    return {"success": True, "data": {"providers": list_providers(category)}}
