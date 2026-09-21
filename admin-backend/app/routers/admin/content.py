from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin, get_db, require_permission
from app.models.admin import Admin
from app.models.content import EducationalContent, FAQ, HomepageBanner, ScrollingMessage, SiteSetting
from app.schemas.content import (
    EducationalContentCreate,
    EducationalContentOut,
    EducationalContentUpdate,
    FAQCreate,
    FAQOut,
    FAQUpdate,
    HomepageBannerCreate,
    HomepageBannerOut,
    HomepageBannerUpdate,
    ScrollingMessageCreate,
    ScrollingMessageOut,
    ScrollingMessageUpdate,
    SiteSettingOut,
    SiteSettingUpdate,
)
from datetime import datetime, timezone
from app.models.audit import AuditLog

router = APIRouter(prefix="/admin/content", tags=["content"])


# --- Site settings (support contact info, hero image, ...) ---
@router.get("/settings", response_model=list[SiteSettingOut])
async def list_settings(current_admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    return [SiteSettingOut.model_validate(r) for r in db.query(SiteSetting).all()]


@router.put("/settings/{key}", response_model=SiteSettingOut)
async def update_setting(
    key: str, payload: SiteSettingUpdate,
    current_admin: Admin = Depends(require_permission("content.settings")),
    db: Session = Depends(get_db),
):
    setting = db.query(SiteSetting).filter(SiteSetting.key == key).first()
    if not setting:
        setting = SiteSetting(key=key, value=payload.value)
        db.add(setting)
    else:
        setting.value = payload.value
    db.flush()
    db.add(AuditLog(actor=current_admin.name, action="site_setting_updated", details=f"{key} updated", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(setting)
    return SiteSettingOut.model_validate(setting)


# --- Homepage banners ---
@router.get("/banners", response_model=list[HomepageBannerOut])
async def list_banners(current_admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    rows = db.query(HomepageBanner).order_by(HomepageBanner.display_order).all()
    return [HomepageBannerOut.model_validate(r) for r in rows]


@router.post("/banners", response_model=HomepageBannerOut, status_code=status.HTTP_201_CREATED)
async def create_banner(
    payload: HomepageBannerCreate,
    current_admin: Admin = Depends(require_permission("content.manage")),
    db: Session = Depends(get_db),
):
    banner = HomepageBanner(**payload.model_dump())
    db.add(banner)
    db.flush()
    db.add(AuditLog(actor=current_admin.name, action="banner_created", details=f"Banner created: {banner.title}", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(banner)
    return HomepageBannerOut.model_validate(banner)


@router.patch("/banners/{banner_id}", response_model=HomepageBannerOut)
async def update_banner(
    banner_id: int, payload: HomepageBannerUpdate,
    current_admin: Admin = Depends(require_permission("content.manage")),
    db: Session = Depends(get_db),
):
    banner = db.get(HomepageBanner, banner_id)
    if not banner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Banner not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(banner, field, value)
    db.flush()
    db.add(AuditLog(actor=current_admin.name, action="banner_updated", details=f"Banner updated: {banner.title}", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(banner)
    return HomepageBannerOut.model_validate(banner)


@router.delete("/banners/{banner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_banner(
    banner_id: int,
    current_admin: Admin = Depends(require_permission("content.delete")),
    db: Session = Depends(get_db),
):
    banner = db.get(HomepageBanner, banner_id)
    if not banner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Banner not found")
    db.delete(banner)
    db.add(AuditLog(actor=current_admin.name, action="banner_deleted", details=f"Banner #{banner_id} deleted", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()


# --- Scrolling messages ---
@router.get("/scrolling-messages", response_model=list[ScrollingMessageOut])
async def list_scrolling_messages(current_admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    rows = db.query(ScrollingMessage).order_by(ScrollingMessage.display_order).all()
    return [ScrollingMessageOut.model_validate(r) for r in rows]


@router.post("/scrolling-messages", response_model=ScrollingMessageOut, status_code=status.HTTP_201_CREATED)
async def create_scrolling_message(
    payload: ScrollingMessageCreate,
    current_admin: Admin = Depends(require_permission("content.manage")),
    db: Session = Depends(get_db),
):
    message = ScrollingMessage(**payload.model_dump())
    db.add(message)
    db.flush()
    db.add(AuditLog(actor=current_admin.name, action="scrolling_message_created", details="Scrolling message created", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(message)
    return ScrollingMessageOut.model_validate(message)


@router.patch("/scrolling-messages/{message_id}", response_model=ScrollingMessageOut)
async def update_scrolling_message(
    message_id: int, payload: ScrollingMessageUpdate,
    current_admin: Admin = Depends(require_permission("content.manage")),
    db: Session = Depends(get_db),
):
    message = db.get(ScrollingMessage, message_id)
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(message, field, value)
    db.flush()
    db.add(AuditLog(actor=current_admin.name, action="scrolling_message_updated", details=f"Message #{message_id} updated", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(message)
    return ScrollingMessageOut.model_validate(message)


@router.delete("/scrolling-messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scrolling_message(
    message_id: int,
    current_admin: Admin = Depends(require_permission("content.delete")),
    db: Session = Depends(get_db),
):
    message = db.get(ScrollingMessage, message_id)
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    db.delete(message)
    db.add(AuditLog(actor=current_admin.name, action="scrolling_message_deleted", details=f"Message #{message_id} deleted", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()


# --- Educational content (per game type) ---
@router.get("/educational", response_model=list[EducationalContentOut])
async def list_educational_content(current_admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    return [EducationalContentOut.model_validate(r) for r in db.query(EducationalContent).all()]


@router.post("/educational", response_model=EducationalContentOut, status_code=status.HTTP_201_CREATED)
async def create_educational_content(
    payload: EducationalContentCreate,
    current_admin: Admin = Depends(require_permission("content.manage")),
    db: Session = Depends(get_db),
):
    content = EducationalContent(**payload.model_dump())
    db.add(content)
    db.flush()
    db.add(AuditLog(actor=current_admin.name, action="educational_content_created", details=f"Content created: {content.title}", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(content)
    return EducationalContentOut.model_validate(content)


@router.patch("/educational/{content_id}", response_model=EducationalContentOut)
async def update_educational_content(
    content_id: int, payload: EducationalContentUpdate,
    current_admin: Admin = Depends(require_permission("content.manage")),
    db: Session = Depends(get_db),
):
    content = db.get(EducationalContent, content_id)
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Educational content not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(content, field, value)
    db.flush()
    db.add(AuditLog(actor=current_admin.name, action="educational_content_updated", details=f"Content updated: {content.title}", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(content)
    return EducationalContentOut.model_validate(content)


@router.delete("/educational/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_educational_content(
    content_id: int,
    current_admin: Admin = Depends(require_permission("content.delete")),
    db: Session = Depends(get_db),
):
    content = db.get(EducationalContent, content_id)
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Educational content not found")
    db.delete(content)
    db.add(AuditLog(actor=current_admin.name, action="educational_content_deleted", details=f"Content #{content_id} deleted", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()


# --- FAQ ---
@router.get("/faqs", response_model=list[FAQOut])
async def list_faqs(current_admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    rows = db.query(FAQ).order_by(FAQ.display_order).all()
    return [FAQOut.model_validate(r) for r in rows]


@router.post("/faqs", response_model=FAQOut, status_code=status.HTTP_201_CREATED)
async def create_faq(
    payload: FAQCreate,
    current_admin: Admin = Depends(require_permission("content.manage")),
    db: Session = Depends(get_db),
):
    faq = FAQ(**payload.model_dump())
    db.add(faq)
    db.flush()
    db.add(AuditLog(actor=current_admin.name, action="faq_created", details="FAQ created", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(faq)
    return FAQOut.model_validate(faq)


@router.patch("/faqs/{faq_id}", response_model=FAQOut)
async def update_faq(
    faq_id: int, payload: FAQUpdate,
    current_admin: Admin = Depends(require_permission("content.manage")),
    db: Session = Depends(get_db),
):
    faq = db.get(FAQ, faq_id)
    if not faq:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(faq, field, value)
    db.flush()
    db.add(AuditLog(actor=current_admin.name, action="faq_updated", details=f"FAQ #{faq_id} updated", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    db.refresh(faq)
    return FAQOut.model_validate(faq)


@router.delete("/faqs/{faq_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_faq(
    faq_id: int,
    current_admin: Admin = Depends(require_permission("content.delete")),
    db: Session = Depends(get_db),
):
    faq = db.get(FAQ, faq_id)
    if not faq:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ not found")
    db.delete(faq)
    db.add(AuditLog(actor=current_admin.name, action="faq_deleted", details=f"FAQ #{faq_id} deleted", created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
