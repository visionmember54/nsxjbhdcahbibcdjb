from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_permission
from app.models.admin import Admin
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogOut
from app.schemas.common import Page, PageParams

router = APIRouter(prefix="/admin/audit-logs", tags=["audit"])


@router.get("", response_model=Page[AuditLogOut])
async def list_audit_logs(
    pagination: PageParams = Depends(),
    user_id: int | None = None,
    current_admin: Admin = Depends(require_permission("audit_logs.view")),
    db: Session = Depends(get_db),
):
    query = db.query(AuditLog)
    if user_id is not None:
        query = query.filter(AuditLog.subject_user_id == user_id)
    total = query.count()
    rows = query.order_by(AuditLog.id.desc()).limit(pagination.limit).offset(pagination.offset).all()
    return Page(items=[AuditLogOut.model_validate(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)
