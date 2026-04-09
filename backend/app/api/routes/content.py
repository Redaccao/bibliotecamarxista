from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.api.deps import require_admin
from app.models.user import User
from app.models.log import LogAction
from app.schemas.content import (
    ContentCreate, ContentUpdate, ContentOut,
    CategoryCreate, CategoryUpdate, CategoryOut,
    TagCreate, TagUpdate, TagOut,
)
from app.services import content_service
from app.services.log_service import log_action
from app.utils.pagination import paginate

router = APIRouter(prefix="/admin", tags=["admin-content"])


# ── Conteúdos ─────────────────────────────────────────────────────────────────

@router.post("/contents", response_model=ContentOut, status_code=status.HTTP_201_CREATED)
def create_content(
    payload: ContentCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    content = content_service.create_content(db, payload)
    log_action(db, LogAction.create, admin.id, "content", content.id, f"Criado: {content.title}")
    return content


@router.get("/contents")
def list_contents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    content_type: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    from app.models.content import ContentType
    ct = ContentType(content_type) if content_type else None
    items, total = content_service.list_contents(
        db, page=page, page_size=page_size,
        public_only=False, category_id=category_id, content_type=ct
    )
    return paginate(items, total, page, page_size)


@router.get("/contents/{content_id}", response_model=ContentOut)
def get_content(
    content_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    content = content_service.get_content_by_id(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Conteúdo não encontrado.")
    return content


@router.put("/contents/{content_id}", response_model=ContentOut)
def update_content(
    content_id: int,
    payload: ContentUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    content = content_service.update_content(db, content_id, payload)
    if not content:
        raise HTTPException(status_code=404, detail="Conteúdo não encontrado.")
    log_action(db, LogAction.update, admin.id, "content", content_id, f"Editado: {content.title}")
    return content


@router.delete("/contents/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_content(
    content_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    content = content_service.soft_delete_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Conteúdo não encontrado.")
    log_action(db, LogAction.delete, admin.id, "content", content_id, "Soft delete")


@router.patch("/contents/{content_id}/publish", response_model=ContentOut)
def publish(
    content_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    content = content_service.publish_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Conteúdo não encontrado.")
    log_action(db, LogAction.publish, admin.id, "content", content_id)
    return content


@router.patch("/contents/{content_id}/unpublish", response_model=ContentOut)
def unpublish(
    content_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    content = content_service.unpublish_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Conteúdo não encontrado.")
    log_action(db, LogAction.unpublish, admin.id, "content", content_id)
    return content


@router.patch("/contents/{content_id}/feature", response_model=ContentOut)
def feature_content(
    content_id: int,
    featured: bool = Query(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    content = content_service.toggle_featured(db, content_id, featured)
    if not content:
        raise HTTPException(status_code=404, detail="Conteúdo não encontrado.")
    action = LogAction.feature if featured else LogAction.unfeature
    log_action(db, action, admin.id, "content", content_id)
    return content


# ── Categorias ────────────────────────────────────────────────────────────────

@router.post("/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    from app.models.category import Category
    from app.utils.sanitizer import slugify

    slug = slugify(payload.slug or payload.name)
    existing = db.query(Category).filter(Category.slug == slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="Categoria com este slug já existe.")

    cat = Category(name=payload.name.strip(), slug=slug, description=payload.description, color=payload.color)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    log_action(db, LogAction.create, admin.id, "category", cat.id, cat.name)
    return cat


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    from app.models.category import Category
    return db.query(Category).filter(Category.deleted_at.is_(None)).order_by(Category.name).all()


@router.put("/categories/{cat_id}", response_model=CategoryOut)
def update_category(
    cat_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    from app.models.category import Category
    cat = db.query(Category).filter(Category.id == cat_id, Category.deleted_at.is_(None)).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")
    if payload.name:
        cat.name = payload.name.strip()
    if payload.slug:
        from app.utils.sanitizer import slugify
        cat.slug = slugify(payload.slug)
    if payload.description is not None:
        cat.description = payload.description
    if payload.color is not None:
        cat.color = payload.color
    db.commit()
    db.refresh(cat)
    log_action(db, LogAction.update, admin.id, "category", cat_id)
    return cat


@router.delete("/categories/{cat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    cat_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    from app.models.category import Category
    from datetime import datetime, timezone
    cat = db.query(Category).filter(Category.id == cat_id, Category.deleted_at.is_(None)).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")
    cat.deleted_at = datetime.now(timezone.utc)
    db.commit()
    log_action(db, LogAction.delete, admin.id, "category", cat_id)


# ── Tags ──────────────────────────────────────────────────────────────────────

@router.post("/tags", response_model=TagOut, status_code=status.HTTP_201_CREATED)
def create_tag(
    payload: TagCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    from app.models.tag import Tag
    from app.utils.sanitizer import slugify

    slug = slugify(payload.slug or payload.name)
    existing = db.query(Tag).filter(Tag.slug == slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="Tag com este slug já existe.")

    tag = Tag(name=payload.name.strip(), slug=slug)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    log_action(db, LogAction.create, admin.id, "tag", tag.id, tag.name)
    return tag


@router.get("/tags", response_model=list[TagOut])
def list_tags(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    from app.models.tag import Tag
    return db.query(Tag).order_by(Tag.name).all()


@router.put("/tags/{tag_id}", response_model=TagOut)
def update_tag(
    tag_id: int,
    payload: TagUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    from app.models.tag import Tag
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag não encontrada.")
    if payload.name:
        tag.name = payload.name.strip()
    if payload.slug:
        from app.utils.sanitizer import slugify
        tag.slug = slugify(payload.slug)
    db.commit()
    db.refresh(tag)
    log_action(db, LogAction.update, admin.id, "tag", tag_id)
    return tag


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    from app.models.tag import Tag
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag não encontrada.")
    db.delete(tag)
    db.commit()
    log_action(db, LogAction.delete, admin.id, "tag", tag_id)
