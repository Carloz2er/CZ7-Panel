from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    username: str

class User(UserBase):
    id: int
    discord_id: str
    avatar: str | None = None

    class Config:
        from_attributes = True