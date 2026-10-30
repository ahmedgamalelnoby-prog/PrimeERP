from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.database.session import get_db
from app.modules.audit.service import record_audit_event
from app.modules.identity.dependencies import get_current_user
from app.modules.branches.membership import BranchUserMembership
from app.modules.companies.membership import CompanyUserMembership
from app.modules.identity.models import User
from app.modules.roles.models import Permission, Role, role_permissions
from app.modules.roles.schemas import (
    PermissionCreate,
    PermissionResponse,
    PermissionUpdate,
    RoleCreate,
    RolePermissionsUpdate,
    RoleResponse,
    RoleStatusUpdate,
    RoleUpdate,
)
from app.modules.roles.services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["Roles & Permissions"])


def require_platform_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform administrator access required")
    return current_user


@router.get("/permissions", response_model=list[PermissionResponse], dependencies=[Depends(require_platform_admin)])
def list_permissions(db: Session = Depends(get_db)) -> list[Permission]:
    return list(db.scalars(select(Permission).order_by(Permission.resource, Permission.action, Permission.name)).all())


@router.post("/permissions", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_platform_admin)])
def create_permission(payload: PermissionCreate, current_user: User = Depends(require_platform_admin), db: Session = Depends(get_db)) -> Permission:
    name = payload.name.strip()
    if db.scalar(select(Permission.id).where(Permission.name == name)) is not None:
        raise HTTPException(status_code=409, detail="Permission name already exists")
    permission = Permission(
        name=name,
        resource=payload.resource.strip(),
        action=payload.action.strip(),
        description=payload.description.strip() if payload.description else None,
        is_active=payload.is_active,
    )
    db.add(permission)
    db.flush()
    record_audit_event(db, action="permission.create", entity_type="permission", entity_id=permission.id, user_id=current_user.id, metadata={"name": permission.name, "resource": permission.resource, "action": permission.action})
    db.commit()
    db.refresh(permission)
    return permission


@router.put("/permissions/{permission_id}", response_model=PermissionResponse, dependencies=[Depends(require_platform_admin)])
def update_permission(permission_id: int, payload: PermissionUpdate, current_user: User = Depends(require_platform_admin), db: Session = Depends(get_db)) -> Permission:
    permission = db.get(Permission, permission_id)
    if permission is None:
        raise HTTPException(status_code=404, detail="Permission was not found")
    data = payload.model_dump(exclude_unset=True)
    for immutable in ("name", "resource", "action"):
        if immutable in data and data[immutable] != getattr(permission, immutable):
            raise HTTPException(status_code=400, detail=f"Permission {immutable} cannot be changed after creation")
    if "description" in data:
        permission.description = data["description"].strip() if data["description"] else None
    if "is_active" in data and data["is_active"] is not None:
        permission.is_active = data["is_active"]
    record_audit_event(db, action="permission.update", entity_type="permission", entity_id=permission.id, user_id=current_user.id, metadata={"changed_fields": sorted(data.keys())})
    db.commit()
    db.refresh(permission)
    return permission


@router.get("/", response_model=list[RoleResponse], dependencies=[Depends(require_platform_admin)])
def list_roles(current_user: User = Depends(require_platform_admin), db: Session = Depends(get_db)) -> list:
    return RoleService(db=db, current_user=current_user).list_roles()


@router.get("/access-audit", dependencies=[Depends(require_platform_admin)])
def get_access_audit(db: Session = Depends(get_db)) -> dict:
    """Summarize role grants and permission coverage for platform administrators."""
    roles = list(
        db.scalars(
            select(Role).options(
                selectinload(Role.permissions)
            ).order_by(Role.name, Role.id)
        ).unique().all()
    )
    permissions = list(
        db.scalars(
            select(Permission).order_by(Permission.resource, Permission.action, Permission.name)
        ).all()
    )

    global_counts = dict(
        db.execute(
            select(User.role_id, func.count(User.id))
            .where(User.role_id.is_not(None), User.is_deleted.is_(False))
            .group_by(User.role_id)
        ).all()
    )
    company_counts = dict(
        db.execute(
            select(CompanyUserMembership.role_id, func.count(CompanyUserMembership.id))
            .where(CompanyUserMembership.role_id.is_not(None))
            .group_by(CompanyUserMembership.role_id)
        ).all()
    )
    branch_counts = dict(
        db.execute(
            select(BranchUserMembership.role_id, func.count(BranchUserMembership.id))
            .where(BranchUserMembership.role_id.is_not(None))
            .group_by(BranchUserMembership.role_id)
        ).all()
    )
    active_role_permission_ids = set(
        db.scalars(
            select(role_permissions.c.permission_id)
            .join(Role, Role.id == role_permissions.c.role_id)
            .where(Role.is_active.is_(True),)
        ).all()
    )

    role_items = []
    findings = []
    for role in roles:
        active_permissions = [p for p in role.permissions if p.is_active]
        inactive_permissions = [p for p in role.permissions if not p.is_active]
        usage = {
            "global_users": int(global_counts.get(role.id, 0)),
            "company_memberships": int(company_counts.get(role.id, 0)),
            "branch_memberships": int(branch_counts.get(role.id, 0)),
        }
        if not role.is_active and sum(usage.values()) > 0:
            findings.append({
                "code": "inactive_role_assigned",
                "severity": "warning",
                "role_id": role.id,
                "role_name": role.name,
                "count": sum(usage.values()),
            })
        if role.is_active and not active_permissions:
            findings.append({
                "code": "active_role_without_permissions",
                "severity": "warning",
                "role_id": role.id,
                "role_name": role.name,
                "count": 0,
            })
        if inactive_permissions:
            findings.append({
                "code": "inactive_permissions_attached",
                "severity": "warning",
                "role_id": role.id,
                "role_name": role.name,
                "count": len(inactive_permissions),
            })
        role_items.append({
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "is_active": role.is_active,
            "permission_count": len(role.permissions),
            "active_permission_count": len(active_permissions),
            "inactive_permission_count": len(inactive_permissions),
            "usage": usage,
        })

    orphan_permissions = [
        permission for permission in permissions
        if permission.is_active and permission.id not in active_role_permission_ids
    ]
    for permission in orphan_permissions:
        findings.append({
            "code": "permission_without_active_role",
            "severity": "info",
            "permission_id": permission.id,
            "permission_name": permission.name,
            "count": 0,
        })

    return {
        "summary": {
            "roles_total": len(roles),
            "roles_active": sum(1 for role in roles if role.is_active),
            "permissions_total": len(permissions),
            "permissions_active": sum(1 for permission in permissions if permission.is_active),
            "permissions_without_active_role": len(orphan_permissions),
            "findings_total": len(findings),
        },
        "roles": role_items,
        "permissions_without_active_role": [
            {
                "id": permission.id,
                "name": permission.name,
                "resource": permission.resource,
                "action": permission.action,
                "description": permission.description,
            }
            for permission in orphan_permissions
        ],
        "findings": findings,
    }


@router.get("/{role_id}", response_model=RoleResponse, dependencies=[Depends(require_platform_admin)])
def get_role(role_id: int, current_user: User = Depends(require_platform_admin), db: Session = Depends(get_db)) -> RoleResponse:
    role = RoleService(db=db, current_user=current_user).get_by_id(role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role was not found")
    return role


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_platform_admin)])
def create_role(payload: RoleCreate, current_user: User = Depends(require_platform_admin), db: Session = Depends(get_db)) -> RoleResponse:
    service = RoleService(db=db, current_user=current_user)
    try:
        role = service.create_role(name=payload.name, description=payload.description, permission_ids=payload.permission_ids, is_active=payload.is_active)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    record_audit_event(db, action="role.create", entity_type="role", entity_id=role.id, user_id=current_user.id, metadata={"name": role.name, "permission_ids": payload.permission_ids})
    db.commit()
    return service.get_by_id(role.id)


@router.put("/{role_id}", response_model=RoleResponse, dependencies=[Depends(require_platform_admin)])
def update_role(role_id: int, payload: RoleUpdate, current_user: User = Depends(require_platform_admin), db: Session = Depends(get_db)) -> RoleResponse:
    service = RoleService(db=db, current_user=current_user)
    try:
        role = service.update_role(role_id, name=payload.name, description=payload.description, is_active=payload.is_active, permission_ids=payload.permission_ids)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    record_audit_event(db, action="role.update", entity_type="role", entity_id=role.id, user_id=current_user.id, metadata={"changed_fields": sorted(payload.model_dump(exclude_unset=True).keys())})
    db.commit()
    return service.get_by_id(role.id)


@router.patch("/{role_id}/status", response_model=RoleResponse, dependencies=[Depends(require_platform_admin)])
def change_role_status(role_id: int, payload: RoleStatusUpdate, current_user: User = Depends(require_platform_admin), db: Session = Depends(get_db)) -> RoleResponse:
    service = RoleService(db=db, current_user=current_user)
    try:
        role = service.change_status(role_id, is_active=payload.is_active)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    record_audit_event(db, action="role.status", entity_type="role", entity_id=role.id, user_id=current_user.id, metadata={"is_active": role.is_active})
    db.commit()
    return service.get_by_id(role.id)


@router.put("/{role_id}/permissions", response_model=RoleResponse, dependencies=[Depends(require_platform_admin)])
def update_role_permissions(role_id: int, payload: RolePermissionsUpdate, current_user: User = Depends(require_platform_admin), db: Session = Depends(get_db)) -> RoleResponse:
    service = RoleService(db=db, current_user=current_user)
    try:
        role = service.update_permissions(role_id, permission_ids=payload.permission_ids)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    record_audit_event(db, action="role.permissions_update", entity_type="role", entity_id=role.id, user_id=current_user.id, metadata={"permission_ids": payload.permission_ids})
    db.commit()
    return service.get_by_id(role.id)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_platform_admin)])
def delete_role(role_id: int, current_user: User = Depends(require_platform_admin), db: Session = Depends(get_db)) -> Response:
    service = RoleService(db=db, current_user=current_user)
    try:
        service.delete_role(role_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    record_audit_event(db, action="role.delete", entity_type="role", entity_id=role_id, user_id=current_user.id)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
