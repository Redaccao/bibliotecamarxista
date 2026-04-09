from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SAEnum, func
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class LogAction(str, enum.Enum):
    login = "login"
    logout = "logout"
    create = "create"
    update = "update"
    delete = "delete"
    publish = "publish"
    unpublish = "unpublish"
    feature = "feature"
    unfeature = "unfeature"


class AdminLog(Base):
    __tablename__ = "admin_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(SAEnum(LogAction), nullable=False, index=True)
    entity_type = Column(String(100), nullable=True)   # ex: "content", "verbete"
    entity_id = Column(Integer, nullable=True)
    detail = Column(Text, nullable=True)               # JSON ou texto livre
    ip_address = Column(String(45), nullable=True)     # IPv4 ou IPv6

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    user = relationship("User", back_populates="logs")

    def __repr__(self) -> str:
        return f"<AdminLog id={self.id} action={self.action} user_id={self.user_id}>"
