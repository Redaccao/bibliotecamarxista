from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.api.deps import require_admin
from app.models.user import User
from app.models.log import AdminLog, LogAction
from app.utils.pagination import paginate

router = APIRouter(prefix="/admin", tags=["admin-dashboard"])


@router.get("/logs")
def list_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = db.query(AdminLog)

    if action:
        q = q.filter(AdminLog.action == action)
    if entity_type:
        q = q.filter(AdminLog.entity_type == entity_type)

    total = q.count()
    items = (
        q.order_by(AdminLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    def serialize(log: AdminLog) -> dict:
        return {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "detail": log.detail,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }

    return paginate([serialize(i) for i in items], total, page, page_size)


@router.get("/dashboard/stats")
def dashboard_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    from app.models.content import Content
    from app.models.verbete import Verbete

    total_contents = db.query(Content).filter(Content.deleted_at.is_(None)).count()
    published = db.query(Content).filter(
        Content.deleted_at.is_(None), Content.is_published.is_(True)
    ).count()
    featured = db.query(Content).filter(
        Content.deleted_at.is_(None), Content.is_featured.is_(True)
    ).count()
    total_verbetes = db.query(Verbete).filter(Verbete.deleted_at.is_(None)).count()

    return {
        "total_contents": total_contents,
        "published_contents": published,
        "draft_contents": total_contents - published,
        "featured_contents": featured,
        "total_verbetes": total_verbetes,
    }
