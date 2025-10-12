from sqlalchemy import Column, String, BigInteger, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base

class Backup(Base):
    __tablename__ = "backups"

    id = Column(BigInteger, primary_key=True, index=True)
    service_id = Column(BigInteger, ForeignKey("services.id"), nullable=False)
    filename = Column(String, nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    service = relationship("Service")