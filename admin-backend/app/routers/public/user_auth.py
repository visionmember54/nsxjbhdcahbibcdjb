from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.user import UserLogin, UserOut, UserRegister, UserTokenResponse
from app.services import user_auth_service

router = APIRouter(prefix="/auth", tags=["user-auth"])


@router.post("/register", response_model=UserTokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, db: Session = Depends(get_db)):
    user = user_auth_service.register(db, payload.name, payload.phone, payload.email, payload.password)
    db.commit()
    db.refresh(user)
    token, _ = user_auth_service.login(db, payload.phone, payload.password)
    return UserTokenResponse(token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=UserTokenResponse)
async def login(payload: UserLogin, request: Request, db: Session = Depends(get_db)):
    token, user = user_auth_service.login(db, payload.phone, payload.password, request)
    return UserTokenResponse(token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)
