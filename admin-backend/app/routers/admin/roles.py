from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_permission
from app.models.admin import Admin
from app.models.role import Permission, Role, RolePermission
from app.schemas.rbac import PermissionOut, RoleCreate, RoleOut, RolePermissionsUpdate
from datetime import datetime, timezone
from app.models.audit import AuditLog

router = APIRouter(prefix="/admin/roles", tags=["roles"])
permissions_router = APIRouter(prefix="/admin/permissions", tags=["roles"])


def _role_out(db: Session, role: Role) -> RoleOut:
    codes = (
        db.query(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .filter(RolePermission.role_id == role.id)
        .all()
    )
    return RoleOut(id=role.id, slug=role.slug, name=role.name, permissions=sorted(c for c, in codes))


@router.get("", response_model=list[RoleOut])
async def list_roles(
    current_admin: Admin = Depends(require_permission("admins.manage")),
    db: Session = Depends(get_db),
):
    roles = db.query(Role).order_by(Role.id).all()
    return [_role_out(db, r) for r in roles]


@router.post("", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: RoleCreate,
    current_admin: Admin = Depends(require_permission("admins.manage")),
    db: Session = Depends(get_db),
):
    slug = payload.slug.strip().lower()
    if db.query(Role).filter(Role.slug == slug).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A role with this slug already exists")

    role = Role(slug=slug, name=payload.name)
    db.add(role)
    db.flush()
    db.add(AuditLog(actor=current_admin.name, action="role_created", details=f"Role created: {slug}", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(role)
    return _role_out(db, role)


@router.put("/{role_id}/permissions", response_model=RoleOut)
async def set_role_permissions(
    role_id: int,
    payload: RolePermissionsUpdate,
    current_admin: Admin = Depends(require_permission("admins.manage")),
    db: Session = Depends(get_db),
):
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    requested = set(payload.permission_codes)
    permissions = db.query(Permission).filter(Permission.code.in_(requested)).all()
    found_codes = {p.code for p in permissions}
    unknown = requested - found_codes
    if unknown:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown permission code(s): {', '.join(sorted(unknown))}")

    db.query(RolePermission).filter(RolePermission.role_id == role.id).delete()
    db.add_all(RolePermission(role_id=role.id, permission_id=p.id) for p in permissions)
    db.flush()
    db.add(AuditLog(actor=current_admin.name, action="role_permissions_updated", details=f"Role '{role.slug}' permissions set to: {', '.join(sorted(found_codes)) or '(none)'}", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    return _role_out(db, role)


@permissions_router.get("", response_model=list[PermissionOut])
async def list_permissions(
    current_admin: Admin = Depends(require_permission("admins.manage")),
    db: Session = Depends(get_db),
):
    return [PermissionOut.model_validate(p) for p in db.query(Permission).order_by(Permission.code).all()]
