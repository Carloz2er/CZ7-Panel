import enum
from sqlalchemy import Column, String, BigInteger, ForeignKey, Enum
from sqlalchemy.orm import relationship

from app.db.session import Base

class ServiceType(str, enum.Enum):
    MINECRAFT_PAPER = "MINECRAFT_PAPER"
    MINECRAFT_FORGE = "MINECRAFT_FORGE"
    MINECRAFT_VANILLA = "MINECRAFT_VANILLA"
    PYTHON_BOT = "PYTHON_BOT"
    NODEJS_APP = "NODEJS_APP"
    VPS = "VPS"

class Service(Base):
    __tablename__ = "services"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String, nullable=False)
    service_type = Column(Enum(ServiceType), nullable=False)
    owner_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)

    docker_container_id = Column(String, unique=True, nullable=True)
    libvirt_domain_name = Column(String, unique=True, nullable=True)
    # plan_id = Column(BigInteger, ForeignKey("plans.id"), nullable=False) # To be added later

    owner = relationship("User")
    # plan = relationship("Plan")