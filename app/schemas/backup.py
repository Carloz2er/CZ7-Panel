from pydantic import BaseModel
from datetime import datetime

class Backup(BaseModel):
    id: int
    service_id: int
    filename: str
    size_bytes: int
    created_at: datetime

    class Config:
        from_attributes = True