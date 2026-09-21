from __future__ import annotations

from typing import Generator

import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import decode_token
from app.db.base import SessionLocal
from app.models.admin import Admin
from app.models.role import Permission, Role, RolePermission
from app.models.user import User


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_admin(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Admin:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token payload invalid")

    if payload.get("role") == "user":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not an admin token")

    admin = db.query(Admin).filter(Admin.email == email).first()
    if not admin or admin.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin account not found or disabled")
    if payload.get("tv", 0) != admin.token_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session has been revoked")
    return admin


def admin_has_permission(db: Session, admin: Admin, code: str) -> bool:
    return (
        db.query(RolePermission)
        .join(Role, Role.id == RolePermission.role_id)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .filter(Role.slug == admin.role, Permission.code == code)
        .first()
        is not None
    )


def get_admin_permissions(db: Session, admin: Admin) -> list[str]:
    codes = (
        db.query(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .filter(Role.slug == admin.role)
        .all()
    )
    return sorted(c for c, in codes)


def require_permission(code: str, error_code: str | None = None):
    def dependency(current_admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)) -> Admin:
        if not admin_has_permission(db, current_admin, code):
            if error_code:
                raise AppError(error_code, "Access denied", status.HTTP_403_FORBIDDEN)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return current_admin

    return dependency


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if payload.get("role") != "user":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not a user token")

    phone = payload.get("sub")
    if not phone:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token payload invalid")

    user = db.query(User).filter(User.phone == phone).first()
    if not user or user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account not found or disabled")
    
    from datetime import datetime, timezone
    user.last_seen = datetime.now(timezone.utc)
    db.commit()
    
    return user
