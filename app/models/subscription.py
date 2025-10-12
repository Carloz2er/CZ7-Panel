import enum
from sqlalchemy import Column, String, BigInteger, ForeignKey, DateTime, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base

class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    PAST_DUE = "past_due"

class Plan(Base):
    __tablename__ = "plans"
    id = Column(BigInteger, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    price = Column(Float, nullable=False)
    stripe_price_id = Column(String, unique=True, nullable=False)

    # Resource Limits
    ram_mb = Column(BigInteger, nullable=False, default=256)
    cpu_vcore = Column(Float, nullable=False, default=0.5)
    disk_gb = Column(BigInteger, nullable=False, default=1)
    max_services = Column(BigInteger, nullable=False, default=1)

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    plan_id = Column(BigInteger, ForeignKey("plans.id"), nullable=False)
    stripe_subscription_id = Column(String, unique=True, nullable=False)
    status = Column(Enum(SubscriptionStatus), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User")
    plan = relationship("Plan")