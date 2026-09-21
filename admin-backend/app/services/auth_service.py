from __future__ import annotations

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core import ratelimit
from app.core.security import _DUMMY_HASH, create_access_token, verify_password
from app.models.admin import Admin


def login(db: Session, email: str, password: str, request: Request) -> tuple[str, Admin]:
    normalized_email = email.strip().lower()
    ratelimit.check_login_allowed(request, normalized_email)

    admin = db.query(Admin).filter(Admin.email == normalized_email).first()
    # Always run one PBKDF2 verification so a missing account takes as long as a wrong password.
    valid = verify_password(password, admin.password_hash if admin else _DUMMY_HASH)
    if not admin or not valid:
        ratelimit.record_login_failure(request, normalized_email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if admin.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin account is disabled")

    ratelimit.clear_login_failures(normalized_email)
    token = create_access_token(admin.email, admin.role, admin.token_version)
    return token, admin
