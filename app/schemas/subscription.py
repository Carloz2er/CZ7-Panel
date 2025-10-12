from pydantic import BaseModel
from datetime import datetime
from app.models.subscription import SubscriptionStatus

class Plan(BaseModel):
    id: int
    name: str
    price: float
    stripe_price_id: str
    ram_mb: int
    cpu_vcore: float
    disk_gb: int
    max_services: int

    class Config:
        from_attributes = True

class Subscription(BaseModel):
    id: int
    plan: Plan
    status: SubscriptionStatus
    current_period_end: datetime

    class Config:
        from_attributes = True