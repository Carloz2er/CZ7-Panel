from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.sql import func

from app.db.session import Base

class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(String, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())