from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.core.dependencies.database import get_db
from app.modules.identity.dependencies.current_user import get_current_user
from app.modules.identity.models import User
from app.modules.identity.services.user_service import UserService


def get_user_service(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserService:
    """Build a tenant-scoped user service from the authenticated principal."""
    return UserService(
        db=db,
        current_user=current_user,
        current_tenant=get_effective_tenant_id(current_user),
    )
