from sqlalchemy import Column, Integer, String, DateTime, Table, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base


# Tabela de associação many-to-many: content <-> tag
content_tags = Table(
    "content_tags",
    Base.metadata,
    Column("content_id", Integer, ForeignKey("contents.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(110), unique=True, nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    contents = relationship("Content", secondary=content_tags, back_populates="tags", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Tag id={self.id} name={self.name}>"
