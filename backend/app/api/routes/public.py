from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.schemas.content import ContentOut, ContentSummary, CategoryOut
from app.schemas.verbete import VerbeteOut
from app.services import content_service, verbete_service, search_service
from app.utils.pagination import paginate

router = APIRouter(prefix="/public", tags=["public"])


# ── Conteúdos ─────────────────────────────────────────────────────────────────

@router.get("/contents/featured")
def list_featured(
    db: Session = Depends(get_db),
):
    """Lista conteúdos em destaque. DEVE vir ANTES de /contents/{slug}."""
    items, _ = content_service.list_contents(
        db, page=1, page_size=10, featured_only=True
    )
    return [ContentSummary.model_validate(i) for i in items]


@router.get("/contents")
def list_contents_public(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    content_type: Optional[str] = None,
    tag_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    from app.models.content import ContentType
    ct = ContentType(content_type) if content_type else None
    items, total = content_service.list_contents(
        db, page=page, page_size=page_size,
        public_only=True, category_id=category_id,
        content_type=ct, tag_id=tag_id,
    )
    return paginate(
        [ContentSummary.model_validate(i) for i in items],
        total, page, page_size
    )


@router.get("/contents/{slug}", response_model=ContentOut)
def get_content_public(
    slug: str,
    db: Session = Depends(get_db),
):
    content = content_service.get_content_by_slug(db, slug, public_only=True)
    if not content:
        raise HTTPException(status_code=404, detail="Conteúdo não encontrado.")
    return content


# ── Categorias ────────────────────────────────────────────────────────────────

@router.get("/categories", response_model=list[CategoryOut])
def list_categories_public(db: Session = Depends(get_db)):
    from app.models.category import Category
    cats = db.query(Category).filter(Category.deleted_at.is_(None)).order_by(Category.name).all()
    return [CategoryOut.model_validate(c) for c in cats]


# ── Verbetes ──────────────────────────────────────────────────────────────────

@router.get("/verbetes/featured")
def list_featured_verbetes(db: Session = Depends(get_db)):
    """Lista verbetes em destaque. DEVE vir ANTES de /verbetes/{slug}."""
    items, _ = verbete_service.list_verbetes(
        db, page=1, page_size=20, public_only=True, featured_only=True
    )
    return [VerbeteOut.model_validate(i) for i in items]


@router.get("/verbetes")
def list_verbetes_public(
    page: int = Query(1, ge=1),
    page_size: int = Query(40, ge=1, le=100),
    letter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    items, total = verbete_service.list_verbetes(
        db, page=page, page_size=page_size,
        public_only=True, letter=letter
    )
    return paginate(
        [VerbeteOut.model_validate(i) for i in items],
        total, page, page_size
    )


@router.get("/verbetes/{slug}", response_model=VerbeteOut)
def get_verbete_public(
    slug: str,
    db: Session = Depends(get_db),
):
    verbete = verbete_service.get_verbete_by_slug(db, slug, public_only=True)
    if not verbete:
        raise HTTPException(status_code=404, detail="Verbete não encontrado.")
    return verbete


# ── Busca ─────────────────────────────────────────────────────────────────────

@router.get("/search/contents")
def search_contents(
    q: str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    items, total = search_service.search_contents(db, q, page=page, page_size=page_size)
    return paginate(
        [ContentSummary.model_validate(i) for i in items],
        total, page, page_size
    )


@router.get("/search/verbetes")
def search_verbetes(
    q: str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    page_size: int = Query(40, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = search_service.search_verbetes(db, q, page=page, page_size=page_size)
    return paginate(
        [VerbeteOut.model_validate(i) for i in items],
        total, page, page_size
    )
