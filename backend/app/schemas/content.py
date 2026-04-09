from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List
from datetime import datetime
from app.models.content import ContentType


# ── Schemas de Tag (aninhado) ──────────────────────────────────────────────────

class TagOut(BaseModel):
    id: int
    name: str
    slug: str

    model_config = {"from_attributes": True}


# ── Schemas de Categoria (aninhado) ───────────────────────────────────────────

class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str
    color: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Content Create ─────────────────────────────────────────────────────────────

class ContentCreate(BaseModel):
    title: str
    slug: Optional[str] = None
    excerpt: Optional[str] = None
    body: Optional[str] = None
    author: Optional[str] = None
    source_url: Optional[str] = None
    cover_image: Optional[str] = None
    content_type: ContentType = ContentType.artigo
    is_published: bool = False
    is_featured: bool = False
    category_id: Optional[int] = None
    tag_ids: List[int] = []

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("O título não pode estar vazio.")
        if len(v) > 500:
            raise ValueError("O título não pode exceder 500 caracteres.")
        return v

    @field_validator("excerpt")
    @classmethod
    def excerpt_length(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 1000:
            raise ValueError("O excerto não pode exceder 1000 caracteres.")
        return v


# ── Content Update ─────────────────────────────────────────────────────────────

class ContentUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    excerpt: Optional[str] = None
    body: Optional[str] = None
    author: Optional[str] = None
    source_url: Optional[str] = None
    cover_image: Optional[str] = None
    content_type: Optional[ContentType] = None
    is_published: Optional[bool] = None
    is_featured: Optional[bool] = None
    category_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("O título não pode estar vazio.")
        return v


# ── Content Out ────────────────────────────────────────────────────────────────

class ContentOut(BaseModel):
    id: int
    title: str
    slug: str
    excerpt: Optional[str] = None
    body: Optional[str] = None
    author: Optional[str] = None
    source_url: Optional[str] = None
    cover_image: Optional[str] = None
    content_type: ContentType
    is_published: bool
    is_featured: bool
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    category: Optional[CategoryOut] = None
    tags: List[TagOut] = []

    model_config = {"from_attributes": True}


class ContentSummary(BaseModel):
    """Versão resumida para listagens públicas (sem corpo completo)."""
    id: int
    title: str
    slug: str
    excerpt: Optional[str] = None
    author: Optional[str] = None
    cover_image: Optional[str] = None
    content_type: ContentType
    is_featured: bool
    published_at: Optional[datetime] = None
    created_at: datetime
    category: Optional[CategoryOut] = None
    tags: List[TagOut] = []

    model_config = {"from_attributes": True}


# ── Category schemas ───────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("O nome não pode estar vazio.")
        return v


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None


# ── Tag schemas ────────────────────────────────────────────────────────────────

class TagCreate(BaseModel):
    name: str
    slug: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("O nome da tag não pode estar vazio.")
        return v


class TagUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
