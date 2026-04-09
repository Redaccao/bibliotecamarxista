from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class VerbeteCreate(BaseModel):
    term: str
    slug: Optional[str] = None
    definition: str
    is_featured: bool = False
    is_published: bool = True

    @field_validator("term")
    @classmethod
    def term_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("O termo não pode estar vazio.")
        if len(v) > 300:
            raise ValueError("O termo não pode exceder 300 caracteres.")
        return v

    @field_validator("definition")
    @classmethod
    def definition_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("A definição não pode estar vazia.")
        return v


class VerbeteUpdate(BaseModel):
    term: Optional[str] = None
    slug: Optional[str] = None
    definition: Optional[str] = None
    is_featured: Optional[bool] = None
    is_published: Optional[bool] = None

    @field_validator("term")
    @classmethod
    def term_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("O termo não pode estar vazio.")
        return v


class VerbeteOut(BaseModel):
    id: int
    term: str
    slug: str
    definition: str
    letter: str
    is_featured: bool
    is_published: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
