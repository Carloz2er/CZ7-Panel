from sqlalchemy import Column, String, BigInteger, Boolean
from sqlalchemy.orm import relationship

from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    discord_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    avatar = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    tickets = relationship("Ticket", back_populates="owner")