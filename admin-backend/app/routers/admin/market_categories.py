from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin, get_db, require_permission
from app.models.admin import Admin
from app.models.market import MarketCategory
from app.schemas.market import MarketCategoryCreate, MarketCategoryOut
from datetime import datetime, timezone
from app.models.audit import AuditLog

router = APIRouter(prefix="/admin/market-categories", tags=["markets"])


@router.get("", response_model=list[MarketCategoryOut])
async def list_market_categories(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    rows = db.query(MarketCategory).order_by(MarketCategory.display_order).all()
    return [MarketCategoryOut.model_validate(r) for r in rows]


@router.post("", response_model=MarketCategoryOut, status_code=status.HTTP_201_CREATED)
async def create_market_category(
    payload: MarketCategoryCreate,
    current_admin: Admin = Depends(require_permission("market_categories.manage")),
    db: Session = Depends(get_db),
):
    slug = payload.slug.strip().upper()
    if db.query(MarketCategory).filter(MarketCategory.slug == slug).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A category with this slug already exists")

    category = MarketCategory(slug=slug, name=payload.name, display_order=payload.display_order)
    db.add(category)
    db.flush()
    db.add(AuditLog(actor=current_admin.name, action="market_category_created", details=f"Category created: {slug}", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(category)
    return MarketCategoryOut.model_validate(category)
