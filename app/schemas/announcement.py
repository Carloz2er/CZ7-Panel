from pydantic import BaseModel
from datetime import datetime

class AnnouncementBase(BaseModel):
    content: str
    is_active: bool = True

class AnnouncementCreate(AnnouncementBase):
    pass

class AnnouncementUpdate(BaseModel):
    content: str | None = None
    is_active: bool | None = None

class Announcement(AnnouncementBase):
    id: str
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True