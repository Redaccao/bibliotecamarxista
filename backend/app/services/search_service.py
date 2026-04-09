from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc, cast
from sqlalchemy.dialects.postgresql import TSVECTOR

from app.models.content import Content
from app.models.verbete import Verbete


def search_contents(
    db: Session,
    query: str,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[Content], int]:
    """
    Full-text search em conteúdos publicados.
    Usa plainto_tsquery + ts_rank. Fallback para ILIKE se search_vector for NULL.
    """
    tsquery = func.plainto_tsquery("portuguese", query)
    ilike_pattern = f"%{query}%"

    q = (
        db.query(Content)
        .filter(
            Content.deleted_at.is_(None),
            Content.is_published.is_(True),
            or_(
                Content.search_vector.op("@@")(tsquery),
                Content.title.ilike(ilike_pattern),
                Content.excerpt.ilike(ilike_pattern),
            ),
        )
        .order_by(
            # Conteúdos com search_vector válido são ordenados por relevância;
            # os sem vector (NULL) ficam por último com rank 0
            desc(
                func.coalesce(
                    func.ts_rank(Content.search_vector, tsquery),
                    0.0,
                )
            ),
            Content.created_at.desc(),
        )
    )

    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def search_verbetes(
    db: Session,
    query: str,
    page: int = 1,
    page_size: int = 40,
) -> Tuple[List[Verbete], int]:
    """Full-text search em verbetes publicados, com fallback ILIKE."""
    tsquery = func.plainto_tsquery("portuguese", query)
    ilike_pattern = f"%{query}%"

    q = (
        db.query(Verbete)
        .filter(
            Verbete.deleted_at.is_(None),
            Verbete.is_published.is_(True),
            or_(
                Verbete.search_vector.op("@@")(tsquery),
                Verbete.term.ilike(ilike_pattern),
                Verbete.definition.ilike(ilike_pattern),
            ),
        )
        .order_by(
            desc(
                func.coalesce(
                    func.ts_rank(Verbete.search_vector, tsquery),
                    0.0,
                )
            ),
            Verbete.term.asc(),
        )
    )

    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return items, total
