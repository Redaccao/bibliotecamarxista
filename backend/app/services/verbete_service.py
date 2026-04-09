from datetime import datetime, timezone
from typing import Optional, List, Tuple
import unicodedata
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.verbete import Verbete
from app.schemas.verbete import VerbeteCreate, VerbeteUpdate
from app.utils.sanitizer import sanitize_html, slugify


def _extract_letter(term: str) -> str:
    normalized = unicodedata.normalize("NFKD", term).encode("ascii", "ignore").decode("ascii")
    letter = normalized[0].upper() if normalized else "#"
    return letter if letter.isalpha() else "#"


def _ensure_unique_slug(db: Session, base_slug: str, exclude_id: Optional[int] = None) -> str:
    slug = base_slug
    counter = 1
    while True:
        q = db.query(Verbete).filter(Verbete.slug == slug, Verbete.deleted_at.is_(None))
        if exclude_id:
            q = q.filter(Verbete.id != exclude_id)
        if not q.first():
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


def _update_search_vector(db: Session, verbete_id: int, term: str, definition: str) -> None:
    """Actualiza search_vector via SQL nativo."""
    raw_text = f"{term} {definition}"
    db.execute(
        text(
            "UPDATE verbetes "
            "SET search_vector = to_tsvector('portuguese', :raw_text) "
            "WHERE id = :verbete_id"
        ),
        {"raw_text": raw_text, "verbete_id": verbete_id},
    )


def create_verbete(db: Session, data: VerbeteCreate) -> Verbete:
    base_slug = slugify(data.slug or data.term)
    slug = _ensure_unique_slug(db, base_slug)
    clean_def = sanitize_html(data.definition)

    verbete = Verbete(
        term=data.term.strip(),
        slug=slug,
        definition=clean_def,
        letter=_extract_letter(data.term),
        is_featured=data.is_featured,
        is_published=data.is_published,
    )

    db.add(verbete)
    db.flush()  # obtém ID sem commit final

    _update_search_vector(db, verbete.id, data.term, clean_def)

    db.commit()
    db.refresh(verbete)
    return verbete


def update_verbete(db: Session, verbete_id: int, data: VerbeteUpdate) -> Optional[Verbete]:
    verbete = get_verbete_by_id(db, verbete_id)
    if not verbete:
        return None

    if data.term is not None:
        verbete.term = data.term.strip()
        verbete.letter = _extract_letter(data.term)
    if data.slug is not None:
        verbete.slug = _ensure_unique_slug(db, slugify(data.slug), exclude_id=verbete_id)
    if data.definition is not None:
        verbete.definition = sanitize_html(data.definition)
    if data.is_featured is not None:
        verbete.is_featured = data.is_featured
    if data.is_published is not None:
        verbete.is_published = data.is_published

    db.flush()

    _update_search_vector(db, verbete.id, verbete.term, verbete.definition)

    db.commit()
    db.refresh(verbete)
    return verbete


def soft_delete_verbete(db: Session, verbete_id: int) -> Optional[Verbete]:
    verbete = get_verbete_by_id(db, verbete_id)
    if not verbete:
        return None
    verbete.deleted_at = datetime.now(timezone.utc)
    verbete.is_published = False
    db.commit()
    db.refresh(verbete)
    return verbete


def toggle_featured_verbete(db: Session, verbete_id: int, featured: bool) -> Optional[Verbete]:
    verbete = get_verbete_by_id(db, verbete_id)
    if not verbete:
        return None
    verbete.is_featured = featured
    db.commit()
    db.refresh(verbete)
    return verbete


def get_verbete_by_id(db: Session, verbete_id: int) -> Optional[Verbete]:
    return (
        db.query(Verbete)
        .filter(Verbete.id == verbete_id, Verbete.deleted_at.is_(None))
        .first()
    )


def get_verbete_by_slug(db: Session, slug: str, public_only: bool = False) -> Optional[Verbete]:
    q = db.query(Verbete).filter(Verbete.slug == slug, Verbete.deleted_at.is_(None))
    if public_only:
        q = q.filter(Verbete.is_published.is_(True))
    return q.first()


def list_verbetes(
    db: Session,
    page: int = 1,
    page_size: int = 40,
    public_only: bool = False,
    letter: Optional[str] = None,
    featured_only: bool = False,
) -> Tuple[List[Verbete], int]:
    q = db.query(Verbete).filter(Verbete.deleted_at.is_(None))

    if public_only:
        q = q.filter(Verbete.is_published.is_(True))
    if letter:
        q = q.filter(Verbete.letter == letter.upper())
    if featured_only:
        q = q.filter(Verbete.is_featured.is_(True), Verbete.is_published.is_(True))

    total = q.count()
    items = (
        q.order_by(Verbete.term.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total
