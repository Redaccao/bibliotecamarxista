from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Index, func
from sqlalchemy.dialects.postgresql import TSVECTOR
from app.core.database import Base


class Verbete(Base):
    __tablename__ = "verbetes"

    id = Column(Integer, primary_key=True, index=True)
    term = Column(String(300), nullable=False, index=True)
    slug = Column(String(320), unique=True, nullable=False, index=True)
    definition = Column(Text, nullable=False)
    letter = Column(String(1), nullable=False, index=True)  # letra inicial para organização alfabética
    is_featured = Column(Boolean, default=False, nullable=False, index=True)
    is_published = Column(Boolean, default=True, nullable=False, index=True)

    search_vector = Column(TSVECTOR, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_verbetes_search_vector", "search_vector", postgresql_using="gin"),
        Index("ix_verbetes_letter_published", "letter", "is_published"),
    )

    def __repr__(self) -> str:
        return f"<Verbete id={self.id} term={self.term}>"
