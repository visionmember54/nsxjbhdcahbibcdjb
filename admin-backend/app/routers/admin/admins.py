from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_permission
from app.core.security import hash_password
from app.models.admin import Admin
from app.models.role import Role
from app.schemas.admin import AdminCreate, AdminOut, AdminUpdate
from app.schemas.common import Page, PageParams
from datetime import datetime, timezone
from app.models.audit import AuditLog

router = APIRouter(prefix="/admin/admins", tags=["admins"])


def _assert_role_exists(db: Session, role_slug: str) -> None:
    if not db.query(Role).filter(Role.slug == role_slug).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown role '{role_slug}'")


@router.get("", response_model=Page[AdminOut])
async def list_admins(
    pagination: PageParams = Depends(),
    current_admin: Admin = Depends(require_permission("admins.manage")),
    db: Session = Depends(get_db),
):
    total = db.query(Admin).count()
    rows = db.query(Admin).order_by(Admin.id.desc()).limit(pagination.limit).offset(pagination.offset).all()
    return Page(items=[AdminOut.model_validate(a) for a in rows], total=total, limit=pagination.limit, offset=pagination.offset)


@router.post("", response_model=AdminOut, status_code=status.HTTP_201_CREATED)
async def create_admin(
    payload: AdminCreate,
    current_admin: Admin = Depends(require_permission("admins.manage")),
    db: Session = Depends(get_db),
):
    normalized_email = payload.email.strip().lower()
    if db.query(Admin).filter(Admin.email == normalized_email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An admin with this email already exists")
    _assert_role_exists(db, payload.role)

    admin = Admin(
        name=payload.name,
        email=normalized_email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        status="active",
    )
    db.add(admin)
    db.flush()
    db.add(AuditLog(actor=current_admin.name, action="admin_created", details=f"Admin created: {admin.email} ({admin.role}, created_at={datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')})"))
    db.commit()
    db.refresh(admin)
    return AdminOut.model_validate(admin)


@router.patch("/{admin_id}", response_model=AdminOut)
async def update_admin(
    admin_id: int,
    payload: AdminUpdate,
    current_admin: Admin = Depends(require_permission("admins.manage")),
    db: Session = Depends(get_db),
):
    admin = db.get(Admin, admin_id)
    if not admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
    if admin.id == current_admin.id and payload.status == "disabled":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot disable your own account")

    if payload.status is not None:
        admin.status = payload.status
    if payload.role is not None:
        _assert_role_exists(db, payload.role)
        admin.role = payload.role
    if payload.status is not None or payload.role is not None:
        admin.token_version += 1  # revoke existing sessions so the new role/status applies immediately
    db.flush()
    db.add(AuditLog(actor=current_admin.name, action="admin_updated", details=f"Admin updated: {admin.email}", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(admin)
    return AdminOut.model_validate(admin)
