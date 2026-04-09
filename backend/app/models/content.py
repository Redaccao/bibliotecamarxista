from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text,
    ForeignKey, Enum as SAEnum, Index, func
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import TSVECTOR
import enum
from app.core.database import Base
from app.models.tag import content_tags


class ContentType(str, enum.Enum):
    artigo = "artigo"
    livro = "livro"
    video = "video"
    audio = "audio"
    documento = "documento"


class Content(Base):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    slug = Column(String(520), unique=True, nullable=False, index=True)
    excerpt = Column(Text, nullable=True)
    body = Column(Text, nullable=True)
    author = Column(String(255), nullable=True)
    source_url = Column(String(1000), nullable=True)
    cover_image = Column(String(1000), nullable=True)
    content_type = Column(SAEnum(ContentType), default=ContentType.artigo, nullable=False, index=True)

    is_published = Column(Boolean, default=False, nullable=False, index=True)
    is_featured = Column(Boolean, default=False, nullable=False, index=True)

    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)

    # Full-text search vector (populado via trigger ou manualmente)
    search_vector = Column(TSVECTOR, nullable=True)

    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    category = relationship("Category", back_populates="contents")
    tags = relationship("Tag", secondary=content_tags, back_populates="contents", lazy="joined")

    __table_args__ = (
        # Índice GIN para full-text search
        Index("ix_contents_search_vector", "search_vector", postgresql_using="gin"),
        # Índice composto para listagem pública (publicados, não deletados)
        Index("ix_contents_published_active", "is_published", "deleted_at"),
        # Índice para destaques
        Index("ix_contents_featured", "is_featured", "is_published"),
    )

    def __repr__(self) -> str:
        return f"<Content id={self.id} slug={self.slug}>"
