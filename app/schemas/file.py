from pydantic import BaseModel
from datetime import datetime

class FileItem(BaseModel):
    name: str
    path: str
    is_dir: bool
    size_bytes: int
    modified_at: datetime