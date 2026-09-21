from __future__ import annotations

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core import ratelimit
from app.core.security import _DUMMY_HASH, create_access_token, hash_password, verify_password
from app.models.user import User


def register(db: Session, name: str, phone: str, email: str, password: str) -> User:
    if db.query(User).filter(User.phone == phone).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A user with this phone number already exists")

    user = User(name=name, phone=phone, email=email, password_hash=hash_password(password), status="active", balance=0)
    db.add(user)
    db.flush()
    return user


def login(db: Session, phone: str, password: str, request: Request | None = None) -> tuple[str, User]:
    if request is not None:
        ratelimit.check_login_allowed(request, phone)
    user = db.query(User).filter(User.phone == phone).first()
    valid = verify_password(password, user.password_hash if user else _DUMMY_HASH)
    if not user or not valid:
        if request is not None:
            ratelimit.record_login_failure(request, phone)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is disabled")
    ratelimit.clear_login_failures(phone)

    token = create_access_token(user.phone, "user")
    return token, user
