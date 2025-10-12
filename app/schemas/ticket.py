from pydantic import BaseModel
from datetime import datetime

from app.models.ticket import TicketStatus
from app.schemas.user import User

class TicketMessageBase(BaseModel):
    content: str

class TicketMessageCreate(TicketMessageBase):
    pass

class TicketMessage(TicketMessageBase):
    id: int
    author_id: int
    created_at: datetime
    author: User

    class Config:
        from_attributes = True

class TicketBase(BaseModel):
    title: str

class TicketCreate(TicketBase):
    initial_message: str

class Ticket(TicketBase):
    id: int
    owner_id: int
    status: TicketStatus
    created_at: datetime
    updated_at: datetime | None = None
    messages: list[TicketMessage] = []

    class Config:
        from_attributes = True