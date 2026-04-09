from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.content import Content, ContentType
from app.models.tag import Tag
from app.schemas.content import ContentCreate, ContentUpdate
from app.utils.sanitizer import sanitize_html, slugify


def _ensure_unique_slug(db: Session, base_slug: str, exclude_id: Optional[int] = None) -> str:
    slug = base_slug
    counter = 1
    while True:
        q = db.query(Content).filter(Content.slug == slug, Content.deleted_at.is_(None))
        if exclude_id:
            q = q.filter(Content.id != exclude_id)
        if not q.first():
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


def _resolve_tags(db: Session, tag_ids: List[int]) -> List[Tag]:
    if not tag_ids:
        return []
    return db.query(Tag).filter(Tag.id.in_(tag_ids)).all()


def _update_search_vector(db: Session, content_id: int, title: str, excerpt: str, body: str) -> None:
    """Actualiza search_vector via SQL nativo — o PostgreSQL calcula o tsvector correctamente."""
    raw_text = " ".join(filter(None, [title or "", excerpt or "", body or ""]))
    db.execute(
        text(
            "UPDATE contents "
            "SET search_vector = to_tsvector('portuguese', :raw_text) "
            "WHERE id = :content_id"
        ),
        {"raw_text": raw_text, "content_id": content_id},
    )


def create_content(db: Session, data: ContentCreate) -> Content:
    base_slug = slugify(data.slug or data.title)
    slug = _ensure_unique_slug(db, base_slug)

    clean_body = sanitize_html(data.body or "")
    clean_excerpt = sanitize_html(data.excerpt or "")

    content = Content(
        title=data.title.strip(),
        slug=slug,
        excerpt=clean_excerpt or None,
        body=clean_body or None,
        author=data.author,
        source_url=data.source_url,
        cover_image=data.cover_image,
        content_type=data.content_type,
        is_published=data.is_published,
        is_featured=data.is_featured,
        category_id=data.category_id,
        published_at=datetime.now(timezone.utc) if data.is_published else None,
    )
    content.tags = _resolve_tags(db, data.tag_ids)

    db.add(content)
    db.flush()  # obtém ID sem commit final

    _update_search_vector(db, content.id, data.title, clean_excerpt, clean_body)

    db.commit()
    db.refresh(content)
    return content


def update_content(db: Session, content_id: int, data: ContentUpdate) -> Optional[Content]:
    content = get_content_by_id(db, content_id)
    if not content:
        return None

    if data.title is not None:
        content.title = data.title.strip()
    if data.slug is not None:
        content.slug = _ensure_unique_slug(db, slugify(data.slug), exclude_id=content_id)
    if data.excerpt is not None:
        content.excerpt = sanitize_html(data.excerpt) or None
    if data.body is not None:
        content.body = sanitize_html(data.body) or None
    if data.author is not None:
        content.author = data.author
    if data.source_url is not None:
        content.source_url = data.source_url
    if data.cover_image is not None:
        content.cover_image = data.cover_image
    if data.content_type is not None:
        content.content_type = data.content_type
    if data.category_id is not None:
        content.category_id = data.category_id
    if data.tag_ids is not None:
        content.tags = _resolve_tags(db, data.tag_ids)

    if data.is_published is not None:
        if data.is_published and not content.is_published:
            content.published_at = datetime.now(timezone.utc)
        elif not data.is_published:
            content.published_at = None
        content.is_published = data.is_published

    if data.is_featured is not None:
        content.is_featured = data.is_featured

    db.flush()

    _update_search_vector(
        db, content.id,
        content.title,
        content.excerpt or "",
        content.body or "",
    )

    db.commit()
    db.refresh(content)
    return content


def soft_delete_content(db: Session, content_id: int) -> Optional[Content]:
    content = get_content_by_id(db, content_id)
    if not content:
        return None
    content.deleted_at = datetime.now(timezone.utc)
    content.is_published = False
    db.commit()
    db.refresh(content)
    return content


def publish_content(db: Session, content_id: int) -> Optional[Content]:
    content = get_content_by_id(db, content_id)
    if not content:
        return None
    content.is_published = True
    if not content.published_at:
        content.published_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(content)
    return content


def unpublish_content(db: Session, content_id: int) -> Optional[Content]:
    content = get_content_by_id(db, content_id)
    if not content:
        return None
    content.is_published = False
    db.commit()
    db.refresh(content)
    return content


def toggle_featured(db: Session, content_id: int, featured: bool) -> Optional[Content]:
    content = get_content_by_id(db, content_id)
    if not content:
        return None
    content.is_featured = featured
    db.commit()
    db.refresh(content)
    return content


def get_content_by_id(db: Session, content_id: int) -> Optional[Content]:
    return (
        db.query(Content)
        .filter(Content.id == content_id, Content.deleted_at.is_(None))
        .first()
    )


def get_content_by_slug(db: Session, slug: str, public_only: bool = False) -> Optional[Content]:
    q = db.query(Content).filter(Content.slug == slug, Content.deleted_at.is_(None))
    if public_only:
        q = q.filter(Content.is_published.is_(True))
    return q.first()


def list_contents(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    public_only: bool = False,
    category_id: Optional[int] = None,
    content_type: Optional[ContentType] = None,
    tag_id: Optional[int] = None,
    featured_only: bool = False,
) -> Tuple[List[Content], int]:
    q = db.query(Content).filter(Content.deleted_at.is_(None))

    if public_only:
        q = q.filter(Content.is_published.is_(True))
    if category_id:
        q = q.filter(Content.category_id == category_id)
    if content_type:
        q = q.filter(Content.content_type == content_type)
    if tag_id:
        q = q.join(Content.tags).filter(Tag.id == tag_id)
    if featured_only:
        q = q.filter(Content.is_featured.is_(True), Content.is_published.is_(True))

    total = q.count()
    items = (
        q.order_by(Content.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total
