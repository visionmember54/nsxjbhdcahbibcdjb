from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.content import EducationalContent, FAQ, HomepageBanner, ScrollingMessage, SiteSetting
from app.schemas.content import EducationalContentOut, FAQOut, HomepageBannerOut, ScrollingMessageOut, SiteSettingOut

router = APIRouter(tags=["public-content"])


@router.get("/homepage", response_model=dict)
async def homepage(db: Session = Depends(get_db)):
    banners = db.query(HomepageBanner).filter(HomepageBanner.enabled.is_(True)).order_by(HomepageBanner.display_order).all()
    messages = db.query(ScrollingMessage).filter(ScrollingMessage.enabled.is_(True)).order_by(ScrollingMessage.display_order).all()
    return {
        "banners": [HomepageBannerOut.model_validate(b) for b in banners],
        "scrollingMessages": [ScrollingMessageOut.model_validate(m) for m in messages],
    }


@router.get("/support", response_model=dict)
async def support_settings(db: Session = Depends(get_db)):
    rows = db.query(SiteSetting).filter(SiteSetting.key.in_(["support_phone", "support_whatsapp", "support_email"])).all()
    settings = {r.key: r.value for r in rows}
    faqs = db.query(FAQ).filter(FAQ.enabled.is_(True)).order_by(FAQ.display_order).all()
    return {"settings": settings, "faqs": [FAQOut.model_validate(f) for f in faqs]}


@router.get("/educational-content", response_model=list[EducationalContentOut])
async def educational_content(game_type_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(EducationalContent)
    if game_type_id is not None:
        query = query.filter(EducationalContent.game_type_id == game_type_id)
    return [EducationalContentOut.model_validate(r) for r in query.all()]
